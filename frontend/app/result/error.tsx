"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ResultError({ reset }: { reset: () => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 space-y-4">
      <h2 className="text-xl font-semibold">예상치 못한 오류가 발생했습니다</h2>
      <p className="text-sm text-muted-foreground">
        잠시 후 다시 시도하거나 입력 조건을 변경해주세요.
      </p>
      <div className="flex gap-2">
        <Button variant="outline" onClick={reset}>
          다시 시도
        </Button>
        <Link href="/">
          <Button>처음으로</Button>
        </Link>
      </div>
    </div>
  );
}
