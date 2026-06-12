# -*- coding: utf-8 -*-
# Author: PrasKaa
# Description: Push entire extension folder to private GitHub repo via REST API (no git required)
# Version: 2.0

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
# C:\Users\prasetyok\Documents\Github\github_config.json
# {
#   "github_token_write": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
#   "github_token_read":  "ghp_yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
#   "repo_owner":         "prasetyok",
#   "repo_name":          "PrasKaaPyKitv2",
#   "local_path":         "C:/Users/prasetyok/AppData/Roaming/pyRevit/Extensions/PyPrasKaa.extension"
# }

CONFIG_PATH = r"C:\Users\prasetyok\Documents\Github\github_config.json"

BRANCH      = "main"
API_BASE    = "https://api.github.com"

# File extensions to include when uploading
INCLUDE_EXTENSIONS = {
    ".py", ".json", ".yaml", ".yml", ".txt", ".md",
    ".xml", ".xaml", ".png", ".jpg", ".jpeg", ".ico",
    ".csv", ".toml", ".cfg", ".ini", ".bat", ".ps1"
}

# Folder/file names to skip entirely
EXCLUDE_NAMES = {
    ".git", "__pycache__", ".pyc", "Thumbs.db", ".DS_Store"
}

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
    """
    Make a GitHub API request using System.Net.HttpWebRequest.
    Returns parsed JSON dict/list, or raises on HTTP error.
    """
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
        err_stream = ex.Response.GetResponseStream() if ex.Response else None
        err_body = ""
        if err_stream:
            err_body = StreamReader(err_stream).ReadToEnd()
        raise Exception("GitHub API error [{}]: {}".format(method, err_body))

    reader = StreamReader(resp.GetResponseStream())
    raw = reader.ReadToEnd()
    resp.Close()
    return json.loads(raw)


def encode_file_base64(filepath):
    """Read a file and return base64-encoded string (GitHub API requirement)."""
    with open(filepath, "rb") as f:
        data = f.read()
    # IronPython 2.7: base64.b64encode returns str
    return base64.b64encode(data)

# ---------------------------------------------------------------------------
# HELPERS — FILE COLLECTION
# ---------------------------------------------------------------------------

def collect_files(root_path):
    """
    Walk the extension folder and return list of (absolute_path, repo_relative_path).
    Skips excluded names and non-included extensions.
    """
    files = []
    root_path = os.path.normpath(root_path)

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip excluded dirs in-place so os.walk doesn't recurse into them
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
            # Relative path from extension root, using forward slashes for GitHub
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

# --- Ask for commit message ---
commit_msg = forms.ask_for_string(
    prompt="Push entire extension folder to GitHub.\n\nEnter commit message:",
    title="PrasKaaPyKitv2 - Push to GitHub",
    default="Update toolkit"
)
if not commit_msg:
    script.exit()

output = script.get_output()
output.print_html("<h3>Push to GitHub via API</h3>")
output.print_html("<p>Repo: <b>{}/{}</b> &rarr; branch <b>{}</b></p>".format(owner, repo, BRANCH))

# ---------------------------------------------------------------------------
# STEP 1 — Get latest commit SHA on main
# ---------------------------------------------------------------------------
output.print_html("<p>[1/5] Getting latest commit SHA...</p>")
try:
    ref_data = api_request("GET", "repos/{}/{}/git/ref/heads/{}".format(owner, repo, BRANCH), token)
    latest_commit_sha = ref_data["object"]["sha"]
    output.print_html("<p>&nbsp;&nbsp;Commit SHA: <code>{}</code></p>".format(latest_commit_sha))
except Exception as e:
    output.print_html("<p style='color:red;'>Failed: {}</p>".format(str(e)))
    forms.alert("Step 1 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 2 — Get base tree SHA from that commit
# ---------------------------------------------------------------------------
output.print_html("<p>[2/5] Getting base tree SHA...</p>")
try:
    commit_data = api_request("GET", "repos/{}/{}/git/commits/{}".format(owner, repo, latest_commit_sha), token)
    base_tree_sha = commit_data["tree"]["sha"]
    output.print_html("<p>&nbsp;&nbsp;Tree SHA: <code>{}</code></p>".format(base_tree_sha))
except Exception as e:
    output.print_html("<p style='color:red;'>Failed: {}</p>".format(str(e)))
    forms.alert("Step 2 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 3 — Upload each file as a blob
# ---------------------------------------------------------------------------
output.print_html("<p>[3/5] Collecting and uploading file blobs...</p>")

all_files = collect_files(local_path)
output.print_html("<p>&nbsp;&nbsp;Found <b>{}</b> files to upload.</p>".format(len(all_files)))

tree_entries = []
failed_files = []

for i, (abs_path, rel_path) in enumerate(all_files):
    try:
        b64_content = encode_file_base64(abs_path)
        blob_data = api_request(
            "POST",
            "repos/{}/{}/git/blobs".format(owner, repo),
            token,
            body={"content": b64_content, "encoding": "base64"}
        )
        tree_entries.append({
            "path": rel_path,
            "mode": "100644",   # regular file
            "type": "blob",
            "sha":  blob_data["sha"]
        })
        # Print progress every 10 files to avoid flooding output
        if (i + 1) % 10 == 0 or (i + 1) == len(all_files):
            output.print_html("<p>&nbsp;&nbsp;Uploaded {}/{} files...</p>".format(i + 1, len(all_files)))
    except Exception as e:
        failed_files.append((rel_path, str(e)))
        output.print_html("<p style='color:orange;'>&nbsp;&nbsp;Skipped: {} — {}</p>".format(rel_path, str(e)))

if failed_files:
    output.print_html("<p style='color:orange;'><b>{} file(s) skipped.</b></p>".format(len(failed_files)))

# ---------------------------------------------------------------------------
# STEP 4 — Create new tree
# ---------------------------------------------------------------------------
output.print_html("<p>[4/5] Creating new tree...</p>")
try:
    tree_data = api_request(
        "POST",
        "repos/{}/{}/git/trees".format(owner, repo),
        token,
        body={
            "base_tree": base_tree_sha,
            "tree": tree_entries
        }
    )
    new_tree_sha = tree_data["sha"]
    output.print_html("<p>&nbsp;&nbsp;New tree SHA: <code>{}</code></p>".format(new_tree_sha))
except Exception as e:
    output.print_html("<p style='color:red;'>Failed: {}</p>".format(str(e)))
    forms.alert("Step 4 failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 5 — Create commit object
# ---------------------------------------------------------------------------
output.print_html("<p>[5/5] Creating commit and updating branch ref...</p>")
try:
    new_commit = api_request(
        "POST",
        "repos/{}/{}/git/commits".format(owner, repo),
        token,
        body={
            "message": commit_msg,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        }
    )
    new_commit_sha = new_commit["sha"]
    output.print_html("<p>&nbsp;&nbsp;New commit SHA: <code>{}</code></p>".format(new_commit_sha))
except Exception as e:
    output.print_html("<p style='color:red;'>Failed: {}</p>".format(str(e)))
    forms.alert("Step 5 (commit) failed:\n{}".format(str(e)), exitscript=True)

# ---------------------------------------------------------------------------
# STEP 6 — Update branch ref to new commit
# ---------------------------------------------------------------------------
try:
    api_request(
        "PATCH",
        "repos/{}/{}/git/refs/heads/{}".format(owner, repo, BRANCH),
        token,
        body={"sha": new_commit_sha, "force": False}
    )
except Exception as e:
    output.print_html("<p style='color:red;'>Failed to update ref: {}</p>".format(str(e)))
    forms.alert("Step 6 (update ref) failed:\n{}".format(str(e)), exitscript=True)

output.print_html(
    "<p style='color:green;'><b>Push successful!</b> "
    "{} files committed to {}/{}@{}</p>".format(len(tree_entries), owner, repo, BRANCH)
)
output.print_html(
    "<p><a href='https://github.com/{}/{}/commit/{}'>View commit on GitHub</a></p>".format(
        owner, repo, new_commit_sha
    )
)