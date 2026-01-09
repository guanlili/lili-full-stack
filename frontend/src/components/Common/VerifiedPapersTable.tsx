import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { ScholarPublication, OpenAPI } from "@/client"
import { useQuery } from "@tanstack/react-query"
import axios from "axios"
import {
    AlertCircle,
    CheckCircle,
    ExternalLink,
    Loader2,
} from "lucide-react"

// Type corresponding to backend PaperDetail
interface PaperDetail {
    title: string
    authors: string[]
    publication_date: string | null
    venue: string | null
    doi: string | null
    source_site: string | null
    url: string
    abstract: string | null
}

function VerifiedPaperRow({ pub }: { pub: ScholarPublication }) {
    // Use React Query for caching and state management per row
    const { data, isLoading, isError, error } = useQuery({
        queryKey: ["paperDetail", pub.link],
        queryFn: async () => {
            if (!pub.link) throw new Error("No link available")
            const token = localStorage.getItem("access_token")
            // Use axios directly or generate client method if available
            // Assuming GET /api/v1/scholar/paper/detail?url=...
            const res = await axios.get<PaperDetail>(
                `${OpenAPI.BASE}/api/v1/scholar/paper/detail`,
                {
                    params: { url: pub.link },
                    headers: { Authorization: `Bearer ${token}` },
                }
            )
            return res.data
        },
        enabled: !!pub.link,
        retry: 1,
        staleTime: 1000 * 60 * 60, // Cache for 1 hour
    })

    return (
        <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
            <td className="p-4 align-middle font-medium">
                <div className="max-w-[400px] truncate" title={data?.title || pub.title}>
                    {data?.title || pub.title}
                </div>
            </td>
            <td className="p-4 align-middle">
                <div className="max-w-[200px] truncate" title={data?.authors.join(", ") || pub.authors || ""}>
                    {data ? data.authors.join(", ") : pub.authors}
                </div>
            </td>
            <td className="p-4 align-middle">
                {data?.publication_date || pub.year}
            </td>
            <td className="p-4 align-middle">
                <div className="max-w-[150px] truncate" title={data?.venue || pub.venue || ""}>
                    {data?.venue || pub.venue}
                </div>
            </td>
            <td className="p-4 align-middle font-mono text-xs">
                {data?.doi || "-"}
            </td>
            <td className="p-4 align-middle">
                {data?.source_site ? (
                    <Badge variant="outline" className="font-normal text-xs">
                        {data.source_site}
                    </Badge>
                ) : (
                    <span className="text-muted-foreground text-xs">-</span>
                )}
            </td>
            <td className="p-4 align-middle">
                {isLoading ? (
                    <div className="flex items-center gap-2 text-muted-foreground text-xs">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Resolving...
                    </div>
                ) : isError ? (
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger>
                                <div className="flex items-center gap-2 text-destructive text-xs cursor-help">
                                    <AlertCircle className="h-3 w-3" />
                                    Failed
                                </div>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>{(error as any)?.response?.data?.detail || (error as any)?.message || "Verification failed"}</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                ) : (
                    <div className="flex items-center gap-2 text-green-600 text-xs font-medium">
                        <CheckCircle className="h-3 w-3" />
                        Verified
                    </div>
                )}
            </td>
            <td className="p-4 align-middle text-right">
                {pub.link && (
                    <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                        <a href={pub.link} target="_blank" rel="noreferrer">
                            <ExternalLink className="h-4 w-4" />
                        </a>
                    </Button>
                )}
            </td>
        </tr>
    )
}

export function VerifiedPapersTable({ publications }: { publications: ScholarPublication[] }) {
    return (
        <Card className="border-border shadow-xl overflow-hidden rounded-2xl bg-card/50 backdrop-blur-sm mt-8">
            <CardContent className="p-0">
                <div className="bg-muted/30 p-4 border-b flex items-center justify-between">
                    <h3 className="font-bold flex items-center gap-2 text-primary">
                        <CheckCircle className="h-4 w-4" />
                        Verified Paper Details
                    </h3>
                    <span className="text-xs text-muted-foreground">
                        Sourced directly from publisher websites
                    </span>
                </div>
                <div className="relative w-full overflow-auto">
                    <table className="w-full caption-bottom text-sm">
                        <thead className="[&_tr]:border-b">
                            <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Title</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Authors</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Date</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Venue</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">DOI</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Source</th>
                                <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                                <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Link</th>
                            </tr>
                        </thead>
                        <tbody className="[&_tr:last-child]:border-0">
                            {publications.map((pub, idx) => (
                                <VerifiedPaperRow key={idx} pub={pub} />
                            ))}
                        </tbody>
                    </table>
                    {publications.length === 0 && (
                        <div className="py-20 text-center text-muted-foreground italic">
                            No publications to verify.
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
