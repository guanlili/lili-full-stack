import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { createColumnHelper } from "@tanstack/react-table"
import { Download, Eraser, History as HistoryIcon, Trash2 } from "lucide-react"
import moment from "moment"
import { toast } from "sonner"
import { ScholarService, type SearchHistory } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_layout/history")({
  component: HistoryPage,
})

function ActionsCell({ id }: { id: string }) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: (historyId: string) =>
      ScholarService.deleteHistoryEntry({ historyId }),
    onSuccess: () => {
      toast.success("History entry deleted")
      queryClient.invalidateQueries({ queryKey: ["search-history"] })
    },
    onError: (err) => {
      toast.error(`Failed to delete entry: ${err.message}`)
    },
  })

  return (
    <Button
      variant="ghost"
      size="icon"
      className="text-destructive hover:text-destructive/90 hover:bg-destructive/10"
      onClick={() => deleteMutation.mutate(id)}
      disabled={deleteMutation.isPending}
      title="Delete"
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  )
}

const columnHelper = createColumnHelper<SearchHistory>()

const columns: any[] = [
  columnHelper.accessor("key", {
    header: "Query",
    cell: (info) => {
      const key = info.getValue()
      try {
        const params = JSON.parse(key)
        return (
          <div className="flex flex-col">
            <span className="font-semibold">{params.q}</span>
            <span className="text-xs text-muted-foreground">
              Year: {params.year}
              {params.as_vis === 0 ? " (Include citations)" : ""}
              {params.hl ? ` [${params.hl}]` : ""}
            </span>
          </div>
        )
      } catch {
        return key
      }
    },
  }),
  columnHelper.accessor("result_summary", {
    header: "Summary",
    cell: (info) => <span className="text-sm">{info.getValue() || "-"}</span>,
  }),
  columnHelper.accessor("source", {
    header: "Source",
    cell: (info) => {
      const val = info.getValue()
      const isCache = val === "cache"
      return (
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${isCache ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}`}
        >
          {isCache ? "CACHE HIT" : "REMOTE"}
        </span>
      )
    },
  }),
  columnHelper.accessor("created_at", {
    header: "Date",
    cell: (info) => {
      const date = info.getValue()
      return date ? moment(date).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
  }),
  columnHelper.display({
    id: "actions",
    header: "Actions",
    cell: (info) => {
      const id = info.row.original.id
      if (!id) return null
      return <ActionsCell id={id} />
    },
  }),
]

function HistoryTableContent() {
  const { data: history, isLoading } = useQuery({
    queryKey: ["search-history"],
    queryFn: () => ScholarService.listSearchHistory({}), // TODO: Add filters if needed
  })

  if (isLoading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading history...
      </div>
    )
  }

  if (!history || history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12 border rounded-lg bg-background/50">
        <div className="rounded-full bg-muted p-4 mb-4">
          <HistoryIcon className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No Search History</h3>
        <p className="text-muted-foreground">
          Perform a scholar search to see it here.
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={history} />
}

function HistoryPage() {
  const queryClient = useQueryClient()

  const clearMutation = useMutation({
    mutationFn: () => ScholarService.clearSearchHistory(),
    onSuccess: () => {
      toast.success("History cleared")
      queryClient.invalidateQueries({ queryKey: ["search-history"] })
    },
    onError: (err) => {
      toast.error(`Failed to clear history: ${err.message}`)
    },
  })

  const handleExport = async (format: "json" | "csv") => {
    try {
      await ScholarService.exportHistory({ format })
      // The response for CSV export is blob/string, but generared client returns 'unknown' or parsed JSON.
      // Actually, if it's CSV, backend returns StreamingResponse.
      // openapi-ts might try to parse it as JSON if not configured otherwise for that endpoint.
      // But we can trigger download via window.open or manual fetch if needed.
      // For now, let's assume JSON download works via blob.

      // Wait, generated client uses `__request` which returns promise.
      // If response is text/csv, we might need to handle it.
      // Simpler: use window.open for download link if cookies/auth allowed?
      // But we use Bearer token.

      // Let's rely on standard fetch for download if client wrapper is tricky for file download.
      // Or just alert "Export not fully implemented in UI yet" if complex.
      // But let's try a simple manual fetch for export.
      toast.info(`Exporting ${format.toUpperCase()}...`)

      // Get token from storage?
      const token = localStorage.getItem("access_token") // Assumption
      const url = `/api/v1/scholar/history/export?format=${format}`

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!res.ok) throw new Error("Export failed")

      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = downloadUrl
      a.download = `search_history.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()

      toast.success("Export successful")
    } catch (e: any) {
      toast.error(`Export failed: ${e.message}`)
    }
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 max-w-7xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Search History</h1>
          <p className="text-muted-foreground">
            Manage your past academic searches and cache
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleExport("json")}>
            <Download className="mr-2 h-4 w-4" /> Export JSON
          </Button>
          <Button variant="outline" onClick={() => handleExport("csv")}>
            <Download className="mr-2 h-4 w-4" /> Export CSV
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">
                <Eraser className="mr-2 h-4 w-4" /> Clear History
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete
                  your entire search history and clear the metadata records.
                  (The cached results might remain in database if not strictly
                  cascaded, but history log will be gone).
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={() => clearMutation.mutate()}>
                  Continue
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="border rounded-md bg-card">
        <HistoryTableContent />
      </div>
    </div>
  )
}
