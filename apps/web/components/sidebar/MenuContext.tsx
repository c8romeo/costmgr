/**
 * apps/web/components/sidebar/MenuContext.tsx — React Context for the
 * tenant's industry and menu list.
 *
 * Story 1.1 — Task 3.4. The provider fetches the canonical
 * `tenant_settings` aggregate from `/api/v1/tenant-settings` on mount
 * (via the api-client wrapper) and exposes `{ industry, menu }` to all
 * dashboard components.
 *
 * No page reload is needed when industry changes — `refresh()` is
 * called from `IndustrySelector` after a successful POST, which keeps
 * the sidebar in sync without a hard navigation.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getTenantSettings, type TenantSettingsResponse } from "@/lib/api-client";
import {
  INDUSTRY_MENU_MAP,
  type Industry,
} from "@/lib/menu-config";

export interface MenuContextValue {
  industry: Industry | null;
  menu: readonly string[];
  // AD-8 deferred: `settingsVersion` is a monotonic counter, not money.
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  settingsVersion: number;
  isLoading: boolean;
  error: string | null;
  /** F-1: forwarded from the Server Component layout for child components
   *  that need to call /completion (CalculatorBanner, CalcButton in settings
   *  wizard, etc.). */
  accessToken: string | undefined;
  refresh: () => Promise<void>;
  /** Optimistic update — used by `IndustrySelector` after a successful POST. */
  setIndustry: (industry: Industry, menu: readonly string[]) => void;
}

const MenuContext = createContext<MenuContextValue | null>(null);

export interface MenuProviderProps {
  children: ReactNode;
  /** Access token read server-side (string) and forwarded across RSC.
   *  When undefined, the context skips fetching. (F-1, F-38.) */
  accessToken?: string;
}

export function MenuProvider({ children, accessToken }: MenuProviderProps) {
  const [industry, setIndustryState] = useState<Industry | null>(null);
  const [menu, setMenu] = useState<readonly string[]>([]);
  const [settingsVersion, setSettingsVersion] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const data: TenantSettingsResponse = await getTenantSettings(accessToken);
      setIndustryState(data.industry);
      setSettingsVersion(data.settings_version);
      setMenu(data.industry ? INDUSTRY_MENU_MAP[data.industry] : []);
    } catch (e) {
      const message = e instanceof Error ? e.message : "업종 정보를 불러오지 못했습니다";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    if (accessToken === undefined) {
      // No token yet — leave defaults; provider is data-ready.
      setIsLoading(false);
      return;
    }
    refresh();
  }, [accessToken, refresh]);

  const setIndustry = useCallback(
    (next: Industry, nextMenu: readonly string[]) => {
      setIndustryState(next);
      setMenu(nextMenu);
    },
    [],
  );

  const value = useMemo<MenuContextValue>(
    () => ({
      industry,
      menu,
      settingsVersion,
      isLoading,
      error,
      accessToken,
      refresh,
      setIndustry,
    }),
    [industry, menu, settingsVersion, isLoading, error, accessToken, refresh, setIndustry],
  );

  return <MenuContext.Provider value={value}>{children}</MenuContext.Provider>;
}

export function useMenuContext(): MenuContextValue {
  const ctx = useContext(MenuContext);
  if (!ctx) {
    throw new Error("useMenuContext must be used within <MenuProvider>");
  }
  return ctx;
}
