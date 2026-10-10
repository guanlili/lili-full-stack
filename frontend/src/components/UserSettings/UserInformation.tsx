import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { UsersService, type UserUpdateMe } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  full_name: z.string().max(30, "姓名最多 30 个字符"),
  email: z.email({ message: "请输入有效的邮箱地址" }),
})

type FormData = z.infer<typeof formSchema>

const UserInformation = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      full_name: currentUser?.full_name ?? "",
      email: currentUser?.email,
    },
  })

  useEffect(() => {
    if (!editMode)
      form.reset({
        full_name: currentUser?.full_name ?? "",
        email: currentUser?.email ?? "",
      })
  }, [currentUser?.full_name, currentUser?.email, editMode, form])

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      UsersService.updateUserMe({ requestBody: data }),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(["currentUser"], updatedUser)
      form.reset({
        full_name: updatedUser.full_name ?? "",
        email: updatedUser.email,
      })
      showSuccessToast("个人资料更新成功")
      toggleEditMode()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const onSubmit = (data: FormData) => {
    const updateData: UserUpdateMe = {}

    // only include fields that have changed
    if (data.full_name !== currentUser?.full_name) {
      updateData.full_name = data.full_name
    }
    if (data.email !== currentUser?.email) {
      updateData.email = data.email
    }

    mutation.mutate(updateData)
  }

  const onCancel = () => {
    form.reset()
    toggleEditMode()
  }

  return (
    <Card className="gap-5 shadow-none">
      <CardHeader className="border-b pb-5">
        <CardTitle>个人资料</CardTitle>
        <CardDescription>
          姓名用于页面展示，邮箱用于登录和找回密码。
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex max-w-xl flex-col gap-5"
          >
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) =>
                editMode ? (
                  <FormItem>
                    <FormLabel>姓名</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        autoComplete="name"
                        placeholder="填写你的姓名"
                        disabled={mutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                ) : (
                  <FormItem>
                    <FormLabel>姓名</FormLabel>
                    <p className="break-words py-2 text-sm">
                      {field.value || "未填写"}
                    </p>
                  </FormItem>
                )
              }
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) =>
                editMode ? (
                  <FormItem>
                    <FormLabel>邮箱</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        autoComplete="email"
                        disabled={mutation.isPending}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                ) : (
                  <FormItem>
                    <FormLabel>邮箱</FormLabel>
                    <p className="break-all py-2 text-sm">{field.value}</p>
                  </FormItem>
                )
              }
            />

            <div className="flex gap-3">
              {editMode ? (
                <>
                  <LoadingButton
                    type="submit"
                    loading={mutation.isPending}
                    disabled={!form.formState.isDirty}
                  >
                    保存资料
                  </LoadingButton>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onCancel}
                    disabled={mutation.isPending}
                  >
                    取消
                  </Button>
                </>
              ) : (
                <Button type="button" onClick={toggleEditMode}>
                  编辑资料
                </Button>
              )}
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}

export default UserInformation
