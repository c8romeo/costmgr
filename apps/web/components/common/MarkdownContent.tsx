/**
 * apps/web/components/common/MarkdownContent.tsx — Minimal Markdown renderer.
 *
 * 1st release launch (cj-style 65번째 진입점 bmad-code-review follow-up).
 *
 * Minimal server-renderable Markdown renderer for legal/ support docs.
 * Supports: ATX headings (#, ##, ###, ####), paragraphs, unordered lists (- *),
 * ordered lists (1.), blockquotes (>), horizontal rules (---), inline `code`,
 * inline **bold** and *italic*, and links ([text](url)).
 *
 * Honest scope: NOT a full CommonMark implementation. Intentionally narrow
 * subset covers the four 1st-release docs (`terms-of-service.md`,
 * `privacy-policy.md`, `support.md`, `faq.md`, `launch-announcement.md`).
 * If new doc content requires features outside this subset, the file must
 * be reviewed manually.
 */
import { Fragment, type JSX } from "react";

interface MarkdownContentProps {
  source: string;
}

type Block =
  | { kind: "heading"; level: 1 | 2 | 3 | 4; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "quote"; text: string }
  | { kind: "hr" };

function parse(source: string): Block[] {
  const lines = source.split(/\r?\n/);
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Blank line → skip.
    if (line.trim() === "") {
      i += 1;
      continue;
    }

    // Heading.
    const headingMatch = line.match(/^(#{1,4})\s+(.*)$/);
    if (headingMatch) {
      const level = headingMatch[1].length as 1 | 2 | 3 | 4;
      blocks.push({ kind: "heading", level, text: headingMatch[2] });
      i += 1;
      continue;
    }

    // Horizontal rule.
    if (/^---+\s*$/.test(line)) {
      blocks.push({ kind: "hr" });
      i += 1;
      continue;
    }

    // Blockquote.
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^>\s?/, ""));
      }
      blocks.push({ kind: "quote", text: buf.join(" ") });
      continue;
    }

    // Unordered list.
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i += 1;
      }
      blocks.push({ kind: "list", ordered: false, items });
      continue;
    }

    // Ordered list.
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i += 1;
      }
      blocks.push({ kind: "list", ordered: true, items });
      continue;
    }

    // Paragraph (consume until blank line / heading / list / quote).
    const buf: string[] = [line];
    i += 1;
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^(#{1,4}\s|[-*]\s|\d+\.\s|>\s?|---+\s*$)/.test(lines[i])
    ) {
      buf.push(lines[i]);
      i += 1;
    }
    blocks.push({ kind: "paragraph", text: buf.join(" ") });
  }

  return blocks;
}

function renderInline(text: string): JSX.Element[] {
  // Tokenize inline: **bold**, *italic*, `code`, [text](url).
  const out: JSX.Element[] = [];
  let rest = text;
  let key = 0;

  while (rest.length > 0) {
    const boldMatch = rest.match(/\*\*([^*]+)\*\*/);
    const italicMatch = !boldMatch && rest.match(/(^|[^*])\*([^*]+)\*/);
    const codeMatch = !boldMatch && rest.match(/`([^`]+)`/);
    const linkMatch = !boldMatch && !codeMatch && rest.match(/\[([^\]]+)\]\(([^)]+)\)/);

    const next = (boldMatch ?? italicMatch ?? codeMatch ?? linkMatch);
    if (!next) {
      out.push(<Fragment key={key++}>{rest}</Fragment>);
      break;
    }
    const start = next.index ?? (rest.indexOf((next as RegExpMatchArray)[0]) ?? 0);
    if (start > 0) {
      out.push(<Fragment key={key++}>{rest.slice(0, start)}</Fragment>);
    }
    const matched = (next as RegExpMatchArray)[0];
    if (boldMatch) {
      out.push(<strong key={key++}>{boldMatch[1]}</strong>);
    } else if (italicMatch) {
      out.push(<em key={key++}>{italicMatch[2]}</em>);
      rest = rest.slice(start + 1); // drop the leading non-* char captured
    } else if (codeMatch) {
      out.push(
        <code
          key={key++}
          style={{ background: "rgba(0,0,0,0.06)", padding: "0 0.25rem", borderRadius: 4 }}
        >
          {codeMatch[1]}
        </code>,
      );
    } else if (linkMatch) {
      out.push(
        <a key={key++} href={linkMatch[2]} style={{ color: "var(--primary, #2563eb)" }}>
          {linkMatch[1]}
        </a>,
      );
    }
    rest = rest.slice(start + matched.length);
  }

  return out;
}

export function MarkdownContent({ source }: MarkdownContentProps) {
  const blocks = parse(source);

  return (
    <article style={{ lineHeight: 1.7 }}>
      {blocks.map((block, idx) => {
        switch (block.kind) {
          case "heading": {
            const sizes: Record<number, string> = {
              1: "2rem",
              2: "1.5rem",
              3: "1.25rem",
              4: "1.1rem",
            };
            const Tag = (`h${block.level}` as unknown) as keyof JSX.IntrinsicElements;
            return (
              <Tag
                key={idx}
                style={{
                  fontSize: sizes[block.level],
                  fontWeight: 700,
                  marginTop: block.level === 1 ? 0 : "1.5rem",
                  marginBottom: "0.75rem",
                }}
              >
                {block.text}
              </Tag>
            );
          }
          case "paragraph":
            return (
              <p key={idx} style={{ marginBottom: "1rem" }}>
                {renderInline(block.text)}
              </p>
            );
          case "list":
            if (block.ordered) {
              return (
                <ol key={idx} style={{ marginBottom: "1rem", paddingLeft: "1.5rem" }}>
                  {block.items.map((item, j) => (
                    <li key={j}>{renderInline(item)}</li>
                  ))}
                </ol>
              );
            }
            return (
              <ul key={idx} style={{ marginBottom: "1rem", paddingLeft: "1.5rem" }}>
                {block.items.map((item, j) => (
                  <li key={j}>{renderInline(item)}</li>
                ))}
              </ul>
            );
          case "quote":
            return (
              <blockquote
                key={idx}
                style={{
                  borderLeft: "4px solid #cbd5e1",
                  paddingLeft: "1rem",
                  margin: "0 0 1rem 0",
                  color: "#475569",
                }}
              >
                {renderInline(block.text)}
              </blockquote>
            );
          case "hr":
            return (
              <hr
                key={idx}
                style={{ border: 0, borderTop: "1px solid #e2e8f0", margin: "1.5rem 0" }}
              />
            );
        }
      })}
    </article>
  );
}