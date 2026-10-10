import { Download, LoaderCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUserExport } from "@/hooks/useUserExport"

export default function UserExport() {
  const { enqueue, jobQuery, download, downloadUrl, downloadRef } =
    useUserExport()
  const job = jobQuery.data
  const busy =
    enqueue.isPending ||
    jobQuery.isLoading ||
    job?.status === "queued" ||
    job?.status === "running"
  const fileId = job?.result?.file_id
  return (
    <div className="flex flex-wrap items-center gap-2">
      {job?.status === "completed" && typeof fileId === "string" ? (
        <>
          <Button
            variant="outline"
            disabled={download.isPending}
            onClick={() => download.mutate(fileId)}
          >
            <Download className="size-4" />
            {download.isPending ? "准备下载…" : "下载 CSV"}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => enqueue.mutate()}>
            重新导出
          </Button>
        </>
      ) : (
        <Button
          variant="outline"
          disabled={busy}
          onClick={() => enqueue.mutate()}
        >
          {busy ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : (
            <Download className="size-4" />
          )}
          {busy ? "正在导出…" : "导出全部用户"}
        </Button>
      )}
      {job?.status === "failed" && (
        <span role="alert" className="text-sm text-destructive">
          导出失败，请重试
        </span>
      )}
      {jobQuery.isError && (
        <Button variant="link" size="sm" onClick={() => jobQuery.refetch()}>
          重试查询导出结果
        </Button>
      )}
      <a
        hidden
        ref={downloadRef}
        href={downloadUrl ?? undefined}
        download="users.csv"
      >
        下载用户 CSV
      </a>
    </div>
  )
}
