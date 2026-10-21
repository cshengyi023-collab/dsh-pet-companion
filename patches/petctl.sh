#!/usr/bin/env bash
# ============================================================
# 鲸鱼娘控制台 —— 通过 dsh-pet 的本机 HTTP 接口指挥桌宠
# 适配: dsh-pet 0.3.7（该版本支持 state / broadcast / anim / whisper / chat / config）
# 用法: bash petctl.sh <命令> [参数...]
# 环境变量: PET_BASE(默认 http://127.0.0.1:19387/dsh-pet-7340)  PET_ID(默认 main)
# ============================================================
BASE="${PET_BASE:-http://127.0.0.1:19387/dsh-pet-7340}"
PET="${PET_ID:-main}"

req() { # method path [json-body]
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    curl -s -X "$method" "$BASE$path" -H 'Content-Type: application/json' --data-binary "$body"
  else
    curl -s -X "$method" "$BASE$path"
  fi
}

json_text() { # 转义成 JSON 字符串
  local s="$1"
  s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n}
  printf '"%s"' "$s"
}

cmd="${1:-help}"
case "$cmd" in
  state)
    req GET /state
    ;;
  say)              # say "文本" [毫秒]
    text="${2:?用法: say \"文本\" [毫秒]}"
    dur="${3:-10000}"
    req POST "/broadcast?pet=$PET" "{\"text\":$(json_text "$text"),\"duration\":$dur}"
    ;;
  whisper)
    req POST "/whisper?pet=$PET"
    ;;
  anim)             # anim "池内动画名"
    name="${2:?用法: anim \"池内动画名\"}"
    req POST "/anim?pet=$PET" "{\"name\":$(json_text "$name")}"
    ;;
  # ---- 常用动作别名（名字来自 config.jsonc 的动画池） ----
  wave)   set -- anim "点击回应-元气挥手" ;;
  shy)    set -- anim "点击回应-害羞惊讶" ;;
  dance)  set -- anim "可爱宅舞" ;;
  spin)   set -- anim "小幅度原地360度旋转展示" ;;
  work)   set -- anim "写代码" ;;
  sleep)  set -- anim "原地小憩沉眠" ;;
  eat)    set -- anim "吃白饭" ;;
  magic)  set -- anim "扑克魔术" ;;
  whale)  set -- anim "蓝鲸现世" ;;
  roam)   set -- anim "螃蟹走路" ;;
  run)    set -- anim "原地左转奔跑" ;;
  stretch) set -- anim "超大伸懒腰" ;;
  help|*)
    cat <<'EOF'
鲸鱼娘控制台 (petctl.sh)  —  dsh-pet 0.3.7
  state                     读当前状态
  say "文本" [毫秒]          让她说一句话（气泡，默认 10 秒）
  whisper                   让她自己生成一句碎碎念（走模型）
  anim "动画名"             点播动画池内任意动画
  别名: wave shy dance spin work sleep eat magic whale roam run stretch
  提示: 0.3.7 没有位置/抛掷/占用锁接口；「显示位置」用 右键她 → 显示位置。
EOF
    ;;
esac
echo
