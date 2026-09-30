import { ShieldCheck } from "lucide-react"
import { Appearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import { Footer } from "./Footer"

interface AuthLayoutProps {
  children: React.ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="grid min-h-svh bg-background lg:grid-cols-[minmax(320px,0.9fr)_minmax(480px,1.1fr)]">
      <aside className="relative hidden overflow-hidden bg-slate-950 text-white lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_20%,rgba(45,212,191,0.2),transparent_32%),radial-gradient(circle_at_85%_80%,rgba(14,165,233,0.2),transparent_36%)]" />
        <div className="absolute -right-24 -top-24 size-72 rounded-full border border-white/10" />
        <div className="absolute -bottom-40 -left-24 size-96 rounded-full border border-white/10" />
        <div className="relative flex w-full flex-col justify-between p-10 xl:p-14">
          <Logo variant="full" className="text-white" asLink={false} />

          <div className="max-w-md">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-sm text-white/80 backdrop-blur-sm">
              <ShieldCheck className="size-4 text-teal-300" />
              安全工作区
            </div>
            <h2 className="text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">
              推动工作向前所需的一切。
            </h2>
            <p className="mt-6 max-w-sm text-base leading-7 text-white/65">
              为下一个项目准备的专注起点，能够随着团队一起成长。
            </p>
          </div>

          <p className="text-sm text-white/45">安全、专注，随时为你准备。</p>
        </div>
      </aside>

      <main className="flex min-h-svh flex-col px-6 py-6 md:px-10 md:py-8">
        <div className="flex items-center justify-between lg:justify-end">
          <div className="lg:hidden">
            <Logo variant="full" className="text-base" asLink={false} />
          </div>
          <Appearance />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[440px] rounded-3xl border bg-card/80 p-6 shadow-xl shadow-slate-950/5 backdrop-blur-sm md:p-8">
            {children}
          </div>
        </div>
        <Footer />
      </main>
    </div>
  )
}
