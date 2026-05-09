"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { HUBS, IATA_CODES } from "@/lib/hubs";
import { formatKRW } from "@/lib/format";

const BUDGET_CAP = 30_000_000;
const DAYS_CAP = 30;

interface InfeasibleBannerProps {
  requiredCountries: string[] | null;
  currentBudget: number;
  currentDays: number;
  onFocusBudget: () => void;
  onFocusDeadline: () => void;
  onFocusCountries: () => void;
}

export function InfeasibleBanner({
  requiredCountries,
  currentBudget,
  currentDays,
  onFocusBudget,
  onFocusDeadline,
  onFocusCountries,
}: InfeasibleBannerProps) {
  const selectedCount = requiredCountries?.length ?? IATA_CODES.length;
  const selectedNames = requiredCountries
    ?.map((iata) => HUBS[iata]?.country_kr)
    .filter(Boolean)
    .join(", ");
  const canDropCountry = (requiredCountries?.length ?? 0) >= 2;

  const budgetMaxed = currentBudget >= BUDGET_CAP;
  const daysMaxed = currentDays >= DAYS_CAP;

  return (
    <Card className="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950">
      <CardContent className="p-6 text-center space-y-3">
        <p className="text-lg font-semibold">경로를 찾을 수 없어요</p>
        <p className="text-sm text-muted-foreground">
          {selectedNames ? (
            <>
              선택한 {selectedCount}개국({selectedNames})을 모두 방문할 경로가 없습니다.
            </>
          ) : (
            <>15개국 모두 방문할 경로가 없습니다.</>
          )}{" "}
          좌측에서 조건을 조정해보세요.
        </p>
        <div className="flex gap-2 justify-center flex-wrap">
          <Button
            variant="outline"
            size="sm"
            disabled={budgetMaxed}
            onClick={onFocusBudget}
          >
            {budgetMaxed
              ? `예산 한계 (${formatKRW(BUDGET_CAP)})`
              : `예산 늘리기 (현재 ${formatKRW(currentBudget)})`}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={daysMaxed}
            onClick={onFocusDeadline}
          >
            {daysMaxed
              ? `기간 한계 (${DAYS_CAP}일)`
              : `기간 늘리기 (현재 ${currentDays}일)`}
          </Button>
          {canDropCountry && (
            <Button variant="outline" size="sm" onClick={onFocusCountries}>
              방문 국가 줄이기 (현재 {selectedCount}개국)
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
