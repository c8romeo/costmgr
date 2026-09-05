"""async def test_ → 프로젝트 규약(asyncio.run) 변환 스크립트.

배경:
  pyproject.toml:156 이 규약을 명시한다 —
    "asyncio: async tests (driven via asyncio.run — no pytest-asyncio plugin needed)"
  그러나 27개 파일 / 184개 테스트 함수가 `async def test_` + `await` 로
  작성되어 pytest-asyncio 를 전제한다. 해당 플러그인이 설치되어 있지 않으므로
  이 테스트들은 작성 이후 한 번도 실행된 적이 없고 전부
  "async def functions are not natively supported" 로 실패한다.

변환 전략 (본문 무손실):
  @pytest.mark.asyncio          →  (삭제)
  async def test_x(...) -> None:   →  def test_x(...) -> None:
      <본문>                            async def _inner() -> None:
                                            <본문 그대로, +4 들여쓰기>
                                        asyncio.run(_inner())

  `await` 표현식을 건드리지 않으므로 다중 라인 호출의 괄호 수술이 불필요하다.
  파라미터(픽스처)는 바깥 sync 함수에 남고 클로저로 참조된다.

사용법:
  python scripts/convert_async_tests.py <파일...>       # 변환 적용
  python scripts/convert_async_tests.py --check <파일...>  # 변환 대상만 보고
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ASYNC_DEF = re.compile(r"^(?P<indent>[ \t]*)async def (?P<rest>test_\w+\s*\()")
MARK_ASYNCIO = re.compile(r"^[ \t]*@pytest\.mark\.asyncio[ \t]*$")


def _find_body_end(lines: list[str], start: int, def_indent: int) -> int:
    """def 라인 다음부터 본문이 끝나는 인덱스(exclusive)를 찾는다."""
    end = start
    for i in range(start, len(lines)):
        line = lines[i]
        if not line.strip():
            continue  # 빈 줄은 본문 경계를 확정하지 않는다
        indent = len(line) - len(line.lstrip())
        if indent <= def_indent:
            break
        end = i + 1
    return end


def convert(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    converted = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # @pytest.mark.asyncio 는 다음 줄이 async def test_ 일 때만 제거
        if MARK_ASYNCIO.match(line):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if ASYNC_DEF.match(nxt):
                i += 1
                continue

        m = ASYNC_DEF.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        indent = m.group("indent")
        def_indent = len(indent)

        # 시그니처가 여러 줄일 수 있으므로 콜론으로 끝나는 줄까지 모은다
        sig_end = i
        while sig_end < len(lines) and not lines[sig_end].rstrip().endswith(":"):
            sig_end += 1
        sig = lines[i : sig_end + 1]
        sig[0] = sig[0].replace("async def ", "def ", 1)

        body_start = sig_end + 1
        body_end = _find_body_end(lines, body_start, def_indent)
        body = lines[body_start:body_end]

        # 선두 docstring 은 바깥 sync 함수에 남긴다 (pytest 리포트 보존).
        doc: list[str] = []
        rest = body
        for j, b in enumerate(body):
            if not b.strip():
                continue
            s = b.lstrip()
            if s.startswith(('"""', "'''")):
                q = s[:3]
                # 한 줄 docstring 인지 여러 줄인지 판별
                if s.count(q) >= 2 and len(s.rstrip()) > 3:
                    doc, rest = body[: j + 1], body[j + 1 :]
                else:
                    for k in range(j + 1, len(body)):
                        if q in body[k]:
                            doc, rest = body[: k + 1], body[k + 1 :]
                            break
            break

        out.extend(sig)
        out.extend(doc)
        out.append(f"{indent}    async def _inner() -> None:\n")
        for b in rest:
            out.append(f"    {b}" if b.strip() else b)
        out.append(f"\n{indent}    asyncio.run(_inner())\n")

        converted += 1
        i = body_end

    result = "".join(out)

    # asyncio import 보강
    if converted and not re.search(r"^import asyncio$", result, re.M):
        result = re.sub(
            r"^(from __future__ import annotations\n\n)",
            r"\1import asyncio\n",
            result,
            count=1,
            flags=re.M,
        )
    return result, converted


def main() -> int:
    args = sys.argv[1:]
    check_only = "--check" in args
    paths = [Path(a) for a in args if a != "--check"]

    total = 0
    for p in paths:
        src = p.read_text(encoding="utf-8")
        new, n = convert(src)
        if n:
            total += n
            print(f"{'[CHECK] ' if check_only else ''}{p}: {n} 함수")
            if not check_only:
                p.write_text(new, encoding="utf-8")
    print(f"\n합계: {total} 함수 / {len(paths)} 파일")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
