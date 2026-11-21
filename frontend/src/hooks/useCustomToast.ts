import { toastError, toastSuccess } from "@/lib/toast"

const useCustomToast = () => {
  return { showSuccessToast: toastSuccess, showErrorToast: toastError }
}

export default useCustomToast
