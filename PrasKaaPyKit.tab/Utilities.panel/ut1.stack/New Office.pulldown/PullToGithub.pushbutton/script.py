# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Pull entire extension folder from private GitHub repo via REST API (no git required)
# Version: 3.0

import os
import json
import base64

from System.Net import HttpWebRequest, WebException
from System.Text import Encoding
from System.IO import StreamReader

from pyrevit import forms, script

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
CONFIG_PATH = r"C:\Users\prasetyok\Documents\Github\github_config.json"
BRANCH      = "main"
API_BASE    = "https://api.github.com"

# ---------------------------------------------------------------------------
# OUTPUT HELPERS
# ---------------------------------------------------------------------------

def step_pending(text):
    output.print_html(
        '<p style="margin:2px 0;font-size:13px;color:#888;">'
        '&#9679;&nbsp;&nbsp;{}</p>'.format(text)
    )

def step_ok(text):
    output.print_html(
        '<p style="margin:2px 0;font-size:13px;color:#7ec86e;">'
        '&#10003;&nbsp;&nbsp;{}</p>'.format(text)
    )

def step_warn(text):
    output.print_html(
        '<p style="margin:2px 0;font-size:13px;color:#e8a838;">'
        '&#9888;&nbsp;&nbsp;{}</p>'.format(text)
    )

def step_error(text):
    output.print_html(
        '<p style="margin:2px 0;font-size:13px;color:#e85c5c;">'
        '&#10007;&nbsp;&nbsp;{}</p>'.format(text)
    )

# ---------------------------------------------------------------------------
# HELPERS — CONFIG
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.isfile(CONFIG_PATH):
        forms.alert(
            "Config file not found:\n{}\n\n"
            "Required keys: github_token_read, repo_owner, repo_name, local_path".format(CONFIG_PATH),
            title="PrasKaaPyKitv2 - Pull from GitHub",
            exitscript=True
        )
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# HELPERS — HTTP
# ---------------------------------------------------------------------------

def api_request(method, endpoint, token, body=None):
    url = "{}/{}".format(API_BASE, endpoint.lstrip("/"))
    req = HttpWebRequest.Create(url)
    req.Method = method
    req.ContentType = "application/json"
    req.Accept = "application/vnd.github+json"
    req.Headers.Add("Authorization", "Bearer {}".format(token))
    req.Headers.Add("X-GitHub-Api-Version", "2022-11-28")
    req.UserAgent = "PrasKaaPyKitv2-pyRevit"

    if body is not None:
        body_bytes = Encoding.UTF8.GetBytes(json.dumps(body))
        req.ContentLength = body_bytes.Length
        stream = req.GetRequestStream()
        stream.Write(body_bytes, 0, body_bytes.Length)
        stream.Close()
    else:
        req.ContentLength = 0

    try:
        resp = req.GetResponse()
    except WebException as ex:
        err_body = ""
        if ex.Response:
            err_body = StreamReader(ex.Response.GetResponseStream()).ReadToEnd()
        raise Exception("GitHub API error [{}]: {}".format(method, err_body))

    raw = StreamReader(resp.GetResponseStream()).ReadToEnd()
    resp.Close()
    return json.loads(raw)


def get_tree_recursive(owner, repo, tree_sha, token):
    data = api_request(
        "GET",
        "repos/{}/{}/git/trees/{}?recursive=1".format(owner, repo, tree_sha),
        token
    )
    return data.get("tree", [])


def download_blob(owner, repo, blob_sha, token):
    data    = api_request("GET", "repos/{}/{}/git/blobs/{}".format(owner, repo, blob_sha), token)
    content = data.get("content", "").replace("\n", "")
    if data.get("encoding", "base64") == "base64":
        return base64.b64decode(content)
    return content.encode("utf-8")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

cfg        = load_config()
token      = cfg.get("github_token_read", "").strip()
owner      = cfg.get("repo_owner", "").strip()
repo       = cfg.get("repo_name", "").strip()
local_path = cfg.get("local_path", "").strip().replace("/", "\\")

if not all([token, owner, repo, local_path]):
    forms.alert(
        "Config incomplete.\nRequired: github_token_read, repo_owner, repo_name, local_path",
        title="PrasKaaPyKitv2 - Pull from GitHub",
        exitscript=True
    )

output = script.get_output()
output.set_width(600)
output.print_html(
    '<h3 style="margin-bottom:4px;">Pull from GitHub</h3>'
    '<p style="font-size:12px;color:#888;margin-bottom:10px;">'
    '{}/{} &rarr; <b>{}</b></p>'.format(owner, repo, BRANCH)
)

# ---------------------------------------------------------------------------
# STEP 1 — Get latest commit SHA
# ---------------------------------------------------------------------------
step_pending("Getting latest commit SHA...")
try:
    ref_data          = api_request("GET", "repos/{}/{}/git/ref/heads/{}".format(owner, repo, BRANCH), token)
    latest_commit_sha = ref_data["object"]["sha"]
    step_ok("Commit SHA: <code>{}</code>".format(latest_commit_sha[:7]))
except Exception as e:
    step_error("Failed: {}".format(str(e)))
    forms.alert("Step 1 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 2 — Fetch recursive file tree
# ---------------------------------------------------------------------------
step_pending("Fetching file tree from GitHub...")
try:
    commit_data = api_request("GET", "repos/{}/{}/git/commits/{}".format(owner, repo, latest_commit_sha), token)
    tree_sha    = commit_data["tree"]["sha"]
    tree_items  = get_tree_recursive(owner, repo, tree_sha, token)
    file_items  = [item for item in tree_items if item.get("type") == "blob"]
    step_ok("Found <b>{}</b> files on GitHub.".format(len(file_items)))
except Exception as e:
    step_error("Failed: {}".format(str(e)))
    forms.alert("Step 2 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 3 — Confirm
# ---------------------------------------------------------------------------
if not forms.alert(
    "This will overwrite local files in:\n{}\n\n"
    "with {} files from {}/{} @ {}.\n\nProceed?".format(
        local_path, len(file_items), owner, repo, BRANCH
    ),
    title="PrasKaaPyKitv2 - Pull from GitHub",
    yes=True, no=True
):
    script.exit()

# ---------------------------------------------------------------------------
# STEP 4 — Download and write files
# ---------------------------------------------------------------------------
step_pending("Downloading and writing {} files...".format(len(file_items)))

success_count = 0
failed_files  = []

for i, item in enumerate(file_items):
    rel_path = item["path"]
    blob_sha = item["sha"]
    abs_path = os.path.join(local_path, rel_path.replace("/", "\\"))
    abs_dir  = os.path.dirname(abs_path)

    try:
        if not os.path.isdir(abs_dir):
            os.makedirs(abs_dir)
        raw_bytes = download_blob(owner, repo, blob_sha, token)
        with open(abs_path, "wb") as f:
            f.write(raw_bytes)
        success_count += 1
    except Exception as e:
        failed_files.append((rel_path, str(e)))

    # Native progress bar — updates in-place, no new text lines
    output.update_progress(i + 1, len(file_items))

# Single result line after download completes
if failed_files:
    step_warn(
        "{} / {} files written &mdash; {} failed".format(
            success_count, len(file_items), len(failed_files)
        )
    )
    for path, err in failed_files:
        output.print_html(
            '<p style="font-size:11px;color:#888;margin:1px 0 1px 20px;">'
            '&#9492; {} &mdash; {}</p>'.format(path, err)
        )
else:
    step_ok("All {} files written to local folder.".format(success_count))

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
output.print_html('<hr style="border:none;border-top:1px solid #333;margin:10px 0;">')
output.print_html(
    '<p style="font-size:13px;color:#7ec86e;font-weight:bold;">'
    '&#10003;&nbsp; Pull complete &mdash; '
    '{} / {} files written locally from <code>{}/{}@{}</code></p>'.format(
        success_count, len(file_items), owner, repo, BRANCH
    )
)
output.print_html(
    '<p style="font-size:12px;color:#888;">'
    'Reload pyRevit to apply script changes.</p>'
)
if failed_files:
    output.print_html(
        '<p style="font-size:12px;color:#e8a838;">'
        '{} file(s) failed to write (see above).</p>'.format(len(failed_files))
    )