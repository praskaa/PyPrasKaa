# -*- coding: utf-8 -*-
__title__   = "Push to GitHub"
__author__  = "PrasKaa"
__doc__ = """Version = 1.0
Date    = 13.06.2026
_____________________________________________________________________
Description:
Pushes entire PrasKaaPyKitv2 extension folder to GitHub repository via API.
Uploads files as Git blobs, creates tree, commits, and updates branch ref.
No local git required — uses GitHub REST API with personal access token.

Supports multi-step progress with HTML output: SHA retrieval, tree creation,
blob upload, commit creation, and ref update. Handles partial upload failure
gracefully with per-file error reporting.

_____________________________________________________________________
How-to:
  1. Ensure github_config.json exists at configured CONFIG_PATH
     Required keys: github_token_write, repo_owner, repo_name, local_path
  2. Run tool
  3. Enter commit message in dialog
  4. Tool uploads all tracked files to repo main branch
  5. View result with commit link in output window
_____________________________________________________________________
Last update:
- 13.06.2026 - 1.0 Initial release
_____________________________________________________________________
Author:  PrasKaa
"""
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

INCLUDE_EXTENSIONS = {
    ".py", ".json", ".yaml", ".yml", ".txt", ".md",
    ".xml", ".xaml", ".png", ".jpg", ".jpeg", ".ico",
    ".csv", ".toml", ".cfg", ".ini", ".bat", ".ps1"
}
EXCLUDE_NAMES = {".git", "__pycache__", ".pyc", "Thumbs.db", ".DS_Store"}

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
            "Required keys: github_token_write, repo_owner, repo_name, local_path".format(CONFIG_PATH),
            title="PrasKaaPyKitv2 - Push to GitHub",
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


def encode_file_base64(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    return base64.b64encode(data)

# ---------------------------------------------------------------------------
# HELPERS — FILE COLLECTION
# ---------------------------------------------------------------------------

def collect_files(root_path):
    files = []
    root_path = os.path.normpath(root_path)
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_NAMES and not d.endswith(".pyc")
        ]
        for fname in filenames:
            if fname in EXCLUDE_NAMES:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in INCLUDE_EXTENSIONS:
                continue
            abs_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(abs_path, root_path).replace("\\", "/")
            files.append((abs_path, rel_path))
    return files

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

cfg        = load_config()
token      = cfg.get("github_token_write", "").strip()
owner      = cfg.get("repo_owner", "").strip()
repo       = cfg.get("repo_name", "").strip()
local_path = cfg.get("local_path", "").strip().replace("/", "\\")

if not all([token, owner, repo, local_path]):
    forms.alert(
        "Config incomplete.\nRequired: github_token_write, repo_owner, repo_name, local_path",
        title="PrasKaaPyKitv2 - Push to GitHub",
        exitscript=True
    )

if not os.path.isdir(local_path):
    forms.alert(
        "local_path does not exist:\n{}".format(local_path),
        title="PrasKaaPyKitv2 - Push to GitHub",
        exitscript=True
    )

commit_msg = forms.ask_for_string(
    prompt="Push entire extension folder to GitHub.\n\nEnter commit message:",
    title="PrasKaaPyKitv2 - Push to GitHub",
    default="Update toolkit"
)
if not commit_msg:
    script.exit()

output = script.get_output()
output.set_width(600)
output.print_html(
    '<h3 style="margin-bottom:4px;">Push to GitHub</h3>'
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
# STEP 2 — Get base tree SHA
# ---------------------------------------------------------------------------
step_pending("Getting base tree SHA...")
try:
    commit_data  = api_request("GET", "repos/{}/{}/git/commits/{}".format(owner, repo, latest_commit_sha), token)
    base_tree_sha = commit_data["tree"]["sha"]
    step_ok("Tree SHA: <code>{}</code>".format(base_tree_sha[:7]))
except Exception as e:
    step_error("Failed: {}".format(str(e)))
    forms.alert("Step 2 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 3 — Upload file blobs
# ---------------------------------------------------------------------------
all_files = collect_files(local_path)
step_pending("Uploading {} files to GitHub...".format(len(all_files)))

tree_entries = []
failed_files = []

for i, (abs_path, rel_path) in enumerate(all_files):
    try:
        b64_content = encode_file_base64(abs_path)
        blob_data   = api_request(
            "POST",
            "repos/{}/{}/git/blobs".format(owner, repo),
            token,
            body={"content": b64_content, "encoding": "base64"}
        )
        tree_entries.append({
            "path": rel_path,
            "mode": "100644",
            "type": "blob",
            "sha":  blob_data["sha"]
        })
    except Exception as e:
        failed_files.append((rel_path, str(e)))

    # Native progress bar — updates in-place, no new text lines
    output.update_progress(i + 1, len(all_files))

# Single result line after upload completes
if failed_files:
    step_warn(
        "{} / {} files uploaded &mdash; {} skipped".format(
            len(tree_entries), len(all_files), len(failed_files)
        )
    )
    for path, err in failed_files:
        output.print_html(
            '<p style="font-size:11px;color:#888;margin:1px 0 1px 20px;">'
            '&#9492; {} &mdash; {}</p>'.format(path, err)
        )
else:
    step_ok("All {} files uploaded.".format(len(all_files)))

# ---------------------------------------------------------------------------
# STEP 4 — Create new tree
# ---------------------------------------------------------------------------
step_pending("Creating new tree...")
try:
    tree_data    = api_request(
        "POST",
        "repos/{}/{}/git/trees".format(owner, repo),
        token,
        body={"base_tree": base_tree_sha, "tree": tree_entries}
    )
    new_tree_sha = tree_data["sha"]
    step_ok("New tree SHA: <code>{}</code>".format(new_tree_sha[:7]))
except Exception as e:
    step_error("Failed: {}".format(str(e)))
    forms.alert("Step 4 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 5 — Create commit + update ref
# ---------------------------------------------------------------------------
step_pending("Creating commit and updating branch ref...")
try:
    new_commit = api_request(
        "POST",
        "repos/{}/{}/git/commits".format(owner, repo),
        token,
        body={
            "message": commit_msg,
            "tree":    new_tree_sha,
            "parents": [latest_commit_sha]
        }
    )
    new_commit_sha = new_commit["sha"]
    api_request(
        "PATCH",
        "repos/{}/{}/git/refs/heads/{}".format(owner, repo, BRANCH),
        token,
        body={"sha": new_commit_sha, "force": False}
    )
    step_ok("Commit SHA: <code>{}</code>".format(new_commit_sha[:7]))
except Exception as e:
    step_error("Failed: {}".format(str(e)))
    forms.alert("Step 5 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
output.print_html('<hr style="border:none;border-top:1px solid #333;margin:10px 0;">')
output.print_html(
    '<p style="font-size:13px;color:#7ec86e;font-weight:bold;">'
    '&#10003;&nbsp; Push complete &mdash; '
    '{} / {} files committed to <code>{}/{}@{}</code></p>'.format(
        len(tree_entries), len(all_files), owner, repo, BRANCH
    )
)
output.print_html(
    '<p style="font-size:11px;color:#888;">'
    '<a href="https://github.com/{}/{}/commit/{}">View commit on GitHub</a></p>'.format(
        owner, repo, new_commit_sha
    )
)
if failed_files:
    output.print_html(
        '<p style="font-size:12px;color:#e8a838;">'
        '{} file(s) were skipped (see above).</p>'.format(len(failed_files))
    )
