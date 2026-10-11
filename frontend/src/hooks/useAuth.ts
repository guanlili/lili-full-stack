import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import {
  type BodyLoginLoginAccessToken as AccessToken,
  Login as LoginService,
  type UserPublic,
  type UserRegister,
  Users as UsersService,
} from "@/client"
import { clearSession, startSession } from "@/lib/session"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: () =>
      UsersService.readUserMe({ throwOnError: true }).then(
        (response) => response.data,
      ),
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ body: data, throwOnError: true }).then(
        (response) => response.data,
      ),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      body: data,
      throwOnError: true,
    }).then((response) => response.data)
    startSession(response)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: handleError.bind(showErrorToast),
  })

  const logout = () => {
    clearSession()
    // 取消进行中的请求并清空全部查询缓存：切换账号时绝不能复用
    // 上一账号的身份、列表与详情缓存（包括请求还在途的慢网络场景）
    queryClient.cancelQueries()
    queryClient.clear()
    navigate({ to: "/login" })
  }

  const logoutAll = async () => {
    await LoginService.logoutAll({ throwOnError: true }).then(
      (response) => response.data,
    )
    logout()
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    logoutAll,
    user,
  }
}

export { isLoggedIn }
export default useAuth
