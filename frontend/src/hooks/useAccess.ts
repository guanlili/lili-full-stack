import { useQuery } from "@tanstack/react-query"
import { Access as AccessService } from "@/client"
import { isLoggedIn } from "@/hooks/useAuth"

export function useAccess() {
  return useQuery({
    queryKey: ["access"],
    queryFn: () =>
      AccessService.readAccess({ throwOnError: true }).then(
        (response) => response.data,
      ),
    enabled: isLoggedIn(),
    staleTime: 0,
    refetchOnWindowFocus: true,
  })
}
