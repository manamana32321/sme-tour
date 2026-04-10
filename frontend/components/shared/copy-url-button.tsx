"use client";

import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export function CopyUrlButton() {
  function handleCopy() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      toast.success("URL이 클립보드에 복사되었습니다");
    });
  }

  return (
    <Button variant="ghost" size="sm" onClick={handleCopy}>
      🔗 공유
    </Button>
  );
}
