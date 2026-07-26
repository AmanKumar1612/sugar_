"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

// Documents management is consolidated in Knowledge Base
export default function DocumentsPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin/knowledge-base");
  }, [router]);
  return null;
}
