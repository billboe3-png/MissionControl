import { useEffect, useState, useCallback } from "react";
import { aiApi, type AISearchResult } from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";

export default function HistoryPage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResult, setSearchResult] =
        useState<AISearchResult | null>(null);
    const [searching, setSearching] = useState(false);
    const [searchError, setSearchError] = useState<string | null>(null);
    const [searchHistory, setSearchHistory] = useState<
        AISearchResult[]
    >([]);

    const handleSearch = useCallback(async () => {
        if (!searchQuery.trim()) return;
        setSearching(true);
        setSearchError(null);
        try {
            const result = await aiApi.search(searchQuery);
            setSearchResult(result);
            setSearchHistory((prev) => [result, ...prev.slice(0, 19)]);
        } catch (e: unknown) {
            setSearchError(
                e instanceof Error ? e.message : "Search failed"
            );
        } finally {
            setSearching(false);
        }
    }, [searchQuery]);

    const exampleQueries = [
        "Why is Exchange slow?",
        "Which servers have low disk space?",
        "What failed overnight?",
        "Show unhealthy Hyper-V hosts.",
        "Why is Active Directory unhealthy?",
    ];

    return (
        <>
            <PageHeader
                title="AI Search & History"
                subtitle="Natural language infrastructure search"
            />

            <div className="dashboard-section">
                <h3>Ask a Question</h3>
                <div className="ai-search-container">
                    <SearchInput
                        value={searchQuery}
                        onChange={setSearchQuery}
                        placeholder="Ask about your infrastructure..."
                    />
                    <button
                        className="btn btn-primary"
                        onClick={handleSearch}
                        disabled={searching || !searchQuery.trim()}
                    >
                        {searching ? "Analyzing..." : "Ask AI"}
                    </button>
                </div>

                <div className="ai-example-queries">
                    <span className="ai-examples-label">
                        Try asking:
                    </span>
                    {exampleQueries.map((q) => (
                        <button
                            key={q}
                            className="ai-example-btn"
                            onClick={() => {
                                setSearchQuery(q);
                            }}
                        >
                            {q}
                        </button>
                    ))}
                </div>

                {searchError && (
                    <div className="error-banner">{searchError}</div>
                )}

                {searchResult && (
                    <div className="ai-search-result">
                        <h4>Answer</h4>
                        <div className="ai-answer-text">
                            {searchResult.answer}
                        </div>
                        <div className="ai-answer-meta">
                            <span className="ai-answer-confidence">
                                Confidence:{" "}
                                {(
                                    searchResult.confidence.score * 100
                                ).toFixed(0)}
                                %
                            </span>
                            <span className="ai-answer-sources">
                                Sources:{" "}
                                {searchResult.sources.join(", ")}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            <div className="dashboard-section">
                <h3>Search History ({searchHistory.length})</h3>
                {searchHistory.length > 0 ? (
                    <div className="ai-history-list">
                        {searchHistory.map((item, idx) => (
                            <div key={idx} className="ai-history-item">
                                <div className="ai-history-query">
                                    Q: {item.query}
                                </div>
                                <div className="ai-history-answer">
                                    A: {item.answer.substring(0, 200)}
                                    {item.answer.length > 200 ? "..." : ""}
                                </div>
                                <div className="ai-history-meta">
                                    Confidence:{" "}
                                    {(
                                        item.confidence.score * 100
                                    ).toFixed(0)}
                                    %
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">
                        No search history yet. Try asking a question above.
                    </p>
                )}
            </div>
        </>
    );
}
