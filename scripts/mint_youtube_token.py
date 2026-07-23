#!/usr/bin/env python3
"""Mint a full-scope YouTube refresh token (youtube.force-ssl) to replace the
upload-only one. Full scope unlocks: editing video descriptions, reading
channel stats for the revenue tracker — while still allowing uploads.

Usage:
  1. python scripts/mint_youtube_token.py <CLIENT_ID>
       → prints a Google consent URL. Open it, approve, and Google shows a code.
  2. python scripts/mint_youtube_token.py <CLIENT_ID> <CLIENT_SECRET> <CODE>
       → exchanges the code and prints the refresh token (store as
         YOUTUBE_REFRESH_TOKEN secret; nothing else changes).
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
REDIRECT = "urn:ietf:wg:oauth:2.0:oob"  # legacy fallback; if rejected use http://localhost


def consent_url(client_id: str, redirect: str = REDIRECT) -> str:
    return ("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent"}))


def exchange(client_id: str, client_secret: str, code: str,
             redirect: str = REDIRECT) -> dict:
    data = urllib.parse.urlencode({
        "client_id": client_id, "client_secret": client_secret, "code": code,
        "grant_type": "authorization_code", "redirect_uri": redirect}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def main() -> None:
    args = sys.argv[1:]
    if len(args) == 1:
        print("Open this URL, approve, copy the code Google shows:\n")
        print(consent_url(args[0]))
        print("\nIf Google rejects the redirect URI, re-run with the URL printed for "
              "http://localhost instead:\n")
        print(consent_url(args[0], "http://localhost"))
        print("\n(after approving you'll land on a dead localhost page — the code is "
              "the ?code=... parameter in the address bar)")
    elif len(args) == 3:
        cid, secret, code = args
        try:
            tok = exchange(cid, secret, urllib.parse.unquote(code))
        except Exception:
            tok = exchange(cid, secret, urllib.parse.unquote(code), "http://localhost")
        rt = tok.get("refresh_token")
        if rt:
            print(f"REFRESH_TOKEN:\n{rt}\n\n"
                  "Store it as the GitHub Actions secret YOUTUBE_REFRESH_TOKEN.")
        else:
            print(f"no refresh_token in response: {tok}")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
