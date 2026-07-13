import type { ReactNode } from "react";
import { useLocation, useParams } from "react-router-dom";

import { resolveBreadcrumbs, type BreadcrumbLabels } from "../../lib/pageBreadcrumbs";
import { Breadcrumb } from "./Breadcrumb";
import { PageHeader, type PageHeaderProps } from "./PageHeader";
import { PageLoadingState } from "./PageLoadingState";

export type PageShellProps = PageHeaderProps & {
  breadcrumbLabels?: BreadcrumbLabels;
  loading?: boolean;
  loadingMessage?: string;
  className?: string;
  children?: ReactNode;
};

export function PageShell({
  title,
  subtitle,
  actions,
  breadcrumbLabels,
  loading = false,
  loadingMessage = "Loading…",
  className,
  children,
}: PageShellProps) {
  const { pathname } = useLocation();
  const params = useParams();
  const breadcrumbs = resolveBreadcrumbs(pathname, params, breadcrumbLabels);

  return (
    <div className={["page-shell", className].filter(Boolean).join(" ")}>
      <Breadcrumb items={breadcrumbs} />
      <PageHeader title={title} subtitle={subtitle} actions={actions} />
      {loading ? <PageLoadingState message={loadingMessage} /> : children}
    </div>
  );
}
