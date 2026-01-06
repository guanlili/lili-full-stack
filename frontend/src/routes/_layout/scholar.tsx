import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { ColumnDef } from "@tanstack/react-table"
import axios from "axios"
import {
    BookOpen,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    ChevronUp,
    Download,
    ExternalLink,
    Filter,
    Layers,
    Quote,
    Search,
    Table as TableIcon,
    User,
} from "lucide-react"
import { useState, useEffect } from "react"

import { ScholarService, OpenAPI, type ScholarPublication } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export const Route = createFileRoute("/_layout/scholar")({
    component: ScholarSearch,
})

// Component for expandable long text
function ExpandableText({ text, limit = 100 }: { text: string; limit?: number }) {
    const [isExpanded, setIsExpanded] = useState(false)
    const shouldTruncate = text && text.length > limit

    if (!text) return null
    if (!shouldTruncate) return <span className="text-xs">{text}</span>

    return (
        <div className="flex flex-col gap-1">
            <span className={`text-xs transition-all duration-300 ${isExpanded ? "" : "line-clamp-2"}`}>
                {text}
            </span>
            <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 w-fit text-[10px] text-primary hover:bg-primary/5"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                {isExpanded ? (
                    <div className="flex items-center gap-1">
                        <ChevronUp className="h-3 w-3" /> Less
                    </div>
                ) : (
                    <div className="flex items-center gap-1">
                        <ChevronDown className="h-3 w-3" /> More
                    </div>
                )}
            </Button>
        </div>
    )
}

const publicationColumns: ColumnDef<ScholarPublication>[] = [
    {
        accessorKey: "title",
        header: "Title",
        cell: ({ row }) => (
            <div className="max-w-[350px] font-bold text-sm">
                {row.original.link ? (
                    <a
                        href={row.original.link}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-primary hover:underline transition-colors block"
                    >
                        <ExpandableText text={row.original.title} limit={80} />
                    </a>
                ) : (
                    <ExpandableText text={row.original.title} limit={80} />
                )}
            </div>
        ),
    },
    {
        accessorKey: "authors",
        header: "Authors",
        cell: ({ row }) => (
            <div className="max-w-[200px]">
                <ExpandableText text={row.original.authors || ""} limit={50} />
            </div>
        ),
    },
    {
        accessorKey: "year",
        header: "Year",
        cell: ({ row }) => (
            <Badge variant="outline" className="font-mono text-[10px] bg-muted/30">
                {row.original.year || "N/A"}
            </Badge>
        ),
    },
    {
        accessorKey: "venue",
        header: "Journal / Conference",
        cell: ({ row }) => (
            <div className="max-w-[180px]">
                <ExpandableText text={row.original.venue || "-"} limit={40} />
            </div>
        ),
    },
    {
        accessorKey: "cited_by",
        header: "Cited By",
        cell: ({ row }) => (
            <div className="flex items-center gap-1.5 font-bold text-primary">
                <Quote className="h-3 w-3 opacity-50" />
                {row.original.cited_by || 0}
            </div>
        ),
    },
    {
        accessorKey: "versions",
        header: "Vers.",
        cell: ({ row }) => (
            <div className="flex items-center gap-1.5 text-muted-foreground font-medium">
                <Layers className="h-3 w-3 opacity-50" />
                {row.original.versions || 1}
            </div>
        ),
    },
]

function ScholarSearch() {
    const [searchTerm, setSearchTerm] = useState("")
    const [query, setQuery] = useState("")
    const [start, setStart] = useState(0)

    // Advanced filters
    const [hl, setHl] = useState("en")
    const [asYlo, setAsYlo] = useState<string>("")
    const [showFilters, setShowFilters] = useState(false)
    const [isExporting, setIsExporting] = useState(false)

    const {
        data: results,
        isLoading,
        isError,
        error,
        isFetching,
    } = useQuery({
        queryKey: ["scholarSearch", query, hl, asYlo, start],
        queryFn: () =>
            ScholarService.searchScholar({
                q: query,
                hl: hl,
                asYlo: asYlo ? parseInt(asYlo) : undefined,
                start: start,
            }),
        enabled: !!query,
    })

    // Reset page when search term or filters change
    useEffect(() => {
        setStart(0)
    }, [query, hl, asYlo])

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchTerm.trim()) {
            setQuery(searchTerm)
        }
    }

    const handleExport = async () => {
        if (!results || results.publications.length === 0) return
        setIsExporting(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await axios.post(`${OpenAPI.BASE}/api/v1/scholar/export`, {
                publications: results.publications,
                filename: `scholar_results_${query}_p${start / 10 + 1}.xlsx`
            }, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                responseType: "blob",
            })

            // Create a blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement("a")
            link.href = url
            link.setAttribute("download", `scholar_results_${query}_p${start / 10 + 1}.xlsx`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
        } catch (err) {
            console.error("Export failed", err)
        } finally {
            setIsExporting(false)
        }
    }

    return (
        <div className="container mx-auto py-8 max-w-7xl px-4">
            <div className="flex flex-col gap-8">
                <div className="space-y-4">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div className="space-y-1">
                            <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
                                Academic Search Agent
                            </h1>
                            <p className="text-xl text-muted-foreground">
                                Precision academic intelligence & data analysis.
                            </p>
                        </div>
                        {results && results.publications.length > 0 && (
                            <Button
                                variant="default"
                                onClick={handleExport}
                                className="rounded-xl font-bold gap-2 shadow-lg shadow-primary/20 h-12"
                                disabled={isExporting}
                            >
                                {isExporting ? (
                                    <div className="h-4 w-4 border-2 border-white/30 border-t-white animate-spin rounded-full"></div>
                                ) : (
                                    <Download className="h-4 w-4" />
                                )}
                                Export Current Page
                            </Button>
                        )}
                    </div>
                </div>

                <div className="flex flex-col gap-4">
                    <form
                        onSubmit={handleSearch}
                        className="flex flex-col sm:flex-row gap-3 p-2 rounded-2xl bg-muted/30 border border-border focus-within:border-primary/50 transition-colors shadow-sm"
                    >
                        <div className="relative flex-1">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <Input
                                placeholder="Search by name or topic (e.g., Junping Du, Deep Learning)..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-12 h-14 text-lg border-none bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                className={`h-14 w-14 rounded-xl ${showFilters ? "bg-primary/10 border-primary text-primary" : ""}`}
                                onClick={() => setShowFilters(!showFilters)}
                            >
                                <Filter className="h-5 w-5" />
                            </Button>
                            <Button
                                type="submit"
                                size="lg"
                                className="h-14 px-8 text-lg font-semibold rounded-xl"
                            >
                                Consult Agent
                            </Button>
                        </div>
                    </form>

                    {showFilters && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-6 rounded-2xl bg-muted/20 border border-border animate-in fade-in slide-in-from-top-4 duration-300">
                            <div className="space-y-2">
                                <label className="text-sm font-bold px-1 text-muted-foreground uppercase tracking-wider">Language (hl)</label>
                                <Select value={hl} onValueChange={setHl}>
                                    <SelectTrigger className="bg-background rounded-xl h-11">
                                        <SelectValue placeholder="Select Language" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="en">English (default)</SelectItem>
                                        <SelectItem value="zh-CN">Chinese (Simplified)</SelectItem>
                                        <SelectItem value="zh-TW">Chinese (Traditional)</SelectItem>
                                        <SelectItem value="ja">Japanese</SelectItem>
                                        <SelectItem value="ko">Korean</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold px-1 text-muted-foreground uppercase tracking-wider">Since Year (as_ylo)</label>
                                <Input
                                    type="number"
                                    placeholder="e.g. 2025"
                                    value={asYlo}
                                    onChange={(e) => setAsYlo(e.target.value)}
                                    className="bg-background rounded-xl h-11"
                                />
                            </div>
                            <div className="flex items-end pb-1">
                                <p className="text-xs text-muted-foreground">
                                    Standardized extraction for authors and publications.
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {(isLoading || (isFetching && query)) && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="relative h-16 w-16">
                            <div className="absolute inset-0 rounded-full border-4 border-primary/20"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                        </div>
                        <p className="text-muted-foreground font-medium animate-pulse">
                            Fetching page {start / 10 + 1}...
                        </p>
                    </div>
                )}

                {isError && (
                    <div className="p-6 bg-destructive/5 text-destructive rounded-2xl border border-destructive/20 flex flex-col gap-2 shadow-sm">
                        <h3 className="font-bold text-lg">Search Failed</h3>
                        <p>
                            {(error as any).body?.detail ||
                                (error as any).message ||
                                "Failed to reach Google Scholar. Try changing the query or filters."}
                        </p>
                    </div>
                )}

                {results && !isFetching && (
                    <Tabs defaultValue="all" className="w-full">
                        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                            <TabsList className="bg-muted/50 p-1 rounded-xl">
                                <TabsTrigger value="all" className="rounded-lg px-6">
                                    Visual Flow
                                </TabsTrigger>
                                <TabsTrigger value="data" className="rounded-lg px-6">
                                    <TableIcon className="h-4 w-4 mr-2" />
                                    Statistics Table
                                </TabsTrigger>
                            </TabsList>

                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={start === 0 || isFetching}
                                    onClick={() => setStart(Math.max(0, start - 10))}
                                    className="rounded-lg h-9 px-3"
                                >
                                    <ChevronLeft className="h-4 w-4 mr-1" /> Prev
                                </Button>
                                <div className="px-3 py-1 bg-muted rounded-lg text-xs font-bold">
                                    Page {start / 10 + 1}
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={results.publications.length < 10 || isFetching}
                                    onClick={() => setStart(start + 10)}
                                    className="rounded-lg h-9 px-3"
                                >
                                    Next <ChevronRight className="h-4 w-4 ml-1" />
                                </Button>
                            </div>
                        </div>

                        <TabsContent value="all" className="space-y-8 animate-in fade-in duration-500">
                            {results.authors.length > 0 && (
                                <div className="space-y-4">
                                    <h3 className="text-xl font-bold flex items-center gap-2 px-2">
                                        <User className="h-5 w-5 text-primary" />
                                        Identity Resolution
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {results.authors.map((author) => (
                                            <AuthorCard key={author.scholar_id} author={author} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {results.publications.length > 0 && (
                                <div className="space-y-4 pt-4">
                                    <h3 className="text-xl font-bold flex items-center gap-2 px-2">
                                        <BookOpen className="h-5 w-5 text-primary" />
                                        Knowledge Assets
                                    </h3>
                                    <div className="space-y-4">
                                        {results.publications.map((pub, idx) => (
                                            <PublicationCard key={idx} pub={pub} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </TabsContent>

                        <TabsContent value="data" className="animate-in fade-in duration-500">
                            <Card className="border-border shadow-xl overflow-hidden rounded-2xl bg-card/50 backdrop-blur-sm">
                                <CardContent className="p-0">
                                    <div className="bg-muted/30 p-4 border-b flex items-center justify-between">
                                        <h3 className="font-bold flex items-center gap-2">
                                            <TableIcon className="h-4 w-4 text-primary" />
                                            Academic Statistics Report (Page {start / 10 + 1})
                                        </h3>
                                    </div>
                                    <DataTable
                                        columns={publicationColumns}
                                        data={results.publications}
                                    />
                                    {results.publications.length === 0 && (
                                        <div className="py-20 text-center text-muted-foreground italic">
                                            No publication data available to tabulate.
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                )}

                {query && !isLoading && !isFetching && results?.count === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center gap-4 bg-muted/20 rounded-3xl border border-dashed border-border">
                        <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center text-muted-foreground">
                            <Search className="h-8 w-8" />
                        </div>
                        <div className="space-y-2">
                            <h3 className="text-xl font-bold">No results found</h3>
                            <p className="text-muted-foreground max-w-sm">
                                We couldn't find any records matching "{query}" on page {start / 10 + 1}.
                            </p>
                            {start > 0 && (
                                <Button variant="link" onClick={() => setStart(0)}>Return to page 1</Button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

function AuthorCard({ author }: { author: any }) {
    return (
        <Card className="group border-border/50 hover:border-primary/50 transition-all hover:shadow-md bg-card/50 backdrop-blur-sm">
            <CardContent className="p-6">
                <div className="flex gap-5">
                    <div className="h-16 w-16 flex-shrink-0 relative rounded-2xl overflow-hidden bg-muted border border-border shadow-inner">
                        {author.url_picture ? (
                            <img
                                src={author.url_picture}
                                alt={author.name}
                                className="h-full w-full object-cover grayscale-[30%] group-hover:grayscale-0 transition-all"
                            />
                        ) : (
                            <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                                <User className="h-8 w-8" />
                            </div>
                        )}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start gap-2">
                            <h4 className="text-lg font-bold truncate group-hover:text-primary transition-colors">
                                {author.name}
                            </h4>
                            <div className="flex gap-2">
                                {author.scholar_id && (
                                    <a
                                        href={`https://scholar.google.com/citations?user=${author.scholar_id}`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="h-8 w-8 flex items-center justify-center rounded-lg bg-muted hover:bg-primary hover:text-white transition-colors"
                                    >
                                        <ExternalLink className="h-4 w-4" />
                                    </a>
                                )}
                            </div>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-1 mt-1 font-medium">
                            {author.affiliation}
                        </p>
                        <div className="mt-3 flex flex-wrap gap-1">
                            {author.interests?.slice(0, 3).map((interest: string) => (
                                <Badge
                                    key={interest}
                                    variant="secondary"
                                    className="text-[10px] py-0 px-2 font-semibold bg-primary/5 text-primary/70 border-primary/10"
                                >
                                    {interest}
                                </Badge>
                            ))}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function PublicationCard({ pub }: { pub: any }) {
    return (
        <Card className="border-border/50 hover:border-primary/50 transition-all hover:shadow-sm bg-card/50">
            <CardContent className="p-6">
                <div className="space-y-3">
                    <div className="flex justify-between items-start gap-4">
                        <div className={`text-lg font-extrabold leading-tight ${pub.link ? "hover:text-primary hover:underline transition-colors" : ""
                            }`}>
                            {pub.link ? (
                                <a href={pub.link} target="_blank" rel="noreferrer">
                                    <ExpandableText text={pub.title || ""} limit={120} />
                                </a>
                            ) : (
                                <ExpandableText text={pub.title || ""} limit={120} />
                            )}
                        </div>
                        {pub.link && (
                            <ExternalLink className="h-4 w-4 flex-shrink-0 text-muted-foreground mt-1 opacity-50 group-hover:opacity-100" />
                        )}
                    </div>
                    <p className="text-sm font-semibold text-primary/80">{pub.authors}</p>
                    <div className="relative">
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary/10 rounded-full"></div>
                        <div className="text-sm text-muted-foreground pl-4 italic leading-relaxed">
                            <ExpandableText text={pub.snippet || ""} limit={150} />
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs font-bold text-muted-foreground pt-1">
                        <span className="flex items-center gap-1.5 bg-muted/50 px-3 py-1.5 rounded-lg border">
                            <BookOpen className="h-3.5 w-3.5" />
                            {pub.venue || "Scholarly Article"}
                            {pub.year ? ` (${pub.year})` : ""}
                        </span>
                        {pub.cited_by !== null && (
                            <span className="flex items-center gap-1.5 bg-primary/5 text-primary px-3 py-1.5 rounded-lg border border-primary/10">
                                <Quote className="h-3.5 w-3.5" />
                                Cited by {pub.cited_by}
                            </span>
                        )}
                        {pub.versions && (
                            <span className="flex items-center gap-1.5 bg-muted/50 px-3 py-1.5 rounded-lg border">
                                <Layers className="h-3.5 w-3.5" />
                                {pub.versions} versions
                            </span>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
