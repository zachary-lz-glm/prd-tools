#!/usr/bin/env bash
# detect_proxy.sh — Auto-detect a working proxy for curl-based downloads.
#
# Usage:
#   source scripts/lib/detect_proxy.sh
#   detect_proxy_for_curl   # exports http_proxy/https_proxy if a working proxy is found
#
# Notes:
#   - Only the curl-facing variables are set. npm and uv do NOT honor SOCKS proxies,
#     so we deliberately do not pretend that exporting socks5:// here makes them work.
#   - macOS only auto-detection (uses `networksetup`). Other platforms fall through
#     to environment-supplied http_proxy/HTTP_PROXY untouched.
#   - On verification failure, prints a single warning line to stderr and returns 0.
#     Callers should treat this as best-effort.

detect_proxy_for_curl() {
  # Already set via env — respect user choice, do not override
  if [ -n "${http_proxy:-}" ] || [ -n "${HTTP_PROXY:-}" ]; then
    return 0
  fi

  command -v networksetup &>/dev/null || return 0

  local _socks="" _http=""
  local _iface
  for _iface in Wi-Fi Ethernet; do
    _socks="$(networksetup -getsocksfirewallproxy "$_iface" 2>/dev/null \
      | awk '/Enabled: Yes/{getline; server=$2; getline; port=$2; print "socks5://"server":"port}' \
      | head -1)" || true
    [ -n "$_socks" ] && break
  done
  for _iface in Wi-Fi Ethernet; do
    _http="$(networksetup -getwebproxy "$_iface" 2>/dev/null \
      | awk '/Enabled: Yes/{getline; server=$2; getline; port=$2; print "http://"server":"port}' \
      | head -1)" || true
    [ -n "$_http" ] && break
  done

  # Prefer SOCKS for GitHub access (corporate HTTP proxies often block GitHub)
  if [ -n "$_socks" ] && curl -fsSL --connect-timeout 3 --max-time 5 \
       --proxy "$_socks" -o /dev/null https://github.com 2>/dev/null; then
    export http_proxy="$_socks"
    export https_proxy="$_socks"
    echo "  Auto-detected proxy (SOCKS, curl only): $_socks"
    return 0
  fi
  if [ -n "$_http" ] && curl -fsSL --connect-timeout 3 --max-time 5 \
       --proxy "$_http" -o /dev/null https://github.com 2>/dev/null; then
    export http_proxy="$_http"
    export https_proxy="$_http"
    echo "  Auto-detected proxy (HTTP, curl only): $_http"
    return 0
  fi

  if [ -n "$_socks$_http" ]; then
    echo "  WARNING: System proxy detected but cannot reach GitHub." >&2
    echo "  SOCKS: ${_socks:-none}  HTTP: ${_http:-none}" >&2
  fi
  return 0
}

# Print proxy notice for users — clarifies that npm/uv won't follow socks
proxy_notice_for_pkg_managers() {
  if [ -n "${http_proxy:-}" ] && [[ "${http_proxy}" == socks* ]]; then
    echo "  Note: npm/uv do not honor socks proxies. PyPI/npm fetches may still fail" >&2
    echo "        even though curl downloads succeed via $http_proxy." >&2
  fi
}
