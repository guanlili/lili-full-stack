import { useMutation, useQuery } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { FilesService, JobsService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

export function useUserExport() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [jobId, setJobId] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const downloadRef = useRef<HTMLAnchorElement>(null)
  const jobQuery = useQuery({
    queryKey: ["user-export-job", jobId],
    queryFn: () => JobsService.readJob({ jobId: jobId! }),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return query.state.error || status === "completed" || status === "failed"
        ? false
        : 2000
    },
  })
  const enqueue = useMutation({
    mutationFn: () => JobsService.enqueueUsersExport(),
    onSuccess: (job) => {
      setJobId(job.id)
      showSuccessToast("用户导出任务已提交")
    },
    onError: handleError.bind(showErrorToast),
  })
  const download = useMutation({
    mutationFn: async (assetId: string) => {
      const contents = await FilesService.downloadFile({ assetId })
      if (typeof contents !== "string")
        throw new Error("Unexpected CSV response")
      return URL.createObjectURL(
        new Blob(["\uFEFF", contents], { type: "text/csv;charset=utf-8" }),
      )
    },
    onSuccess: setDownloadUrl,
    onError: handleError.bind(showErrorToast),
  })
  useEffect(() => {
    if (!downloadUrl) return
    downloadRef.current?.click()
    return () => URL.revokeObjectURL(downloadUrl)
  }, [downloadUrl])

  return { enqueue, jobQuery, download, downloadUrl, downloadRef }
}
