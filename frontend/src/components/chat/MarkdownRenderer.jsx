"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

// Light theme code highlighting
import "highlight.js/styles/github.css";

function CopyButton({ getText }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(getText());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <button onClick={handleCopy} className="code-copy-btn" aria-label={copied ? "Copied" : "Copy code"}>
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  return (
    <div className="prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Code — inline vs block
          code({ node, inline, className, children, ...props }) {
            if (inline) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
            // Block code — wrap pre+code together with copy button
            return (
              <div className="code-block-wrapper">
                <CopyButton getText={() => String(children).replace(/\n$/, "")} />
                <code className={className} {...props}>
                  {children}
                </code>
              </div>
            );
          },
          // Wrap pre so the code-block-wrapper handles it
          pre({ children }) {
            return <pre>{children}</pre>;
          },
          // Scrollable tables
          table({ children }) {
            return (
              <div style={{ overflowX: "auto", width: "100%" }}>
                <table>{children}</table>
              </div>
            );
          },
          // External links open in new tab
          a({ href, children }) {
            const isExternal = href?.startsWith("http");
            return (
              <a
                href={href}
                target={isExternal ? "_blank" : undefined}
                rel={isExternal ? "noopener noreferrer" : undefined}
              >
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
