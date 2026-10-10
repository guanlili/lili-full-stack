import { useQuery } from "@tanstack/react-query"
import { AccessService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"

export function useAccess() {
  return useQuery({
    queryKey: ["access"],
    queryFn: AccessService.readAccess,
    enabled: isLoggedIn(),
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}
