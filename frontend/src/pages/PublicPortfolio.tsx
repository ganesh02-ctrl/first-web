import { useParams } from "react-router-dom";
import AchievementCard from "../components/achievement/AchievementCard";
import { Empty, ErrorState, Spinner } from "../components/common/ui";
import { useApi } from "../hooks/useApi";
import { get } from "../services/api";
import type { Achievement } from "../types";

export default function PublicPortfolio() {
  const { slug } = useParams();
  const { data, loading, error } = useApi(() => get<{ full_name: string; college: string | null; degree: string | null; branch: string | null; achievements: Achievement[] }>(`/public/portfolio/${slug}`), [slug]);
  if (loading) return <Spinner />;
  if (error || !data) return <div className="p-8"><ErrorState message="This portfolio doesn't exist, or its owner has made it private." /></div>;
  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="text-3xl font-bold text-navy-800 dark:text-white">{data.full_name}</h1>
      <p className="mb-6 text-slate-500">{[data.degree, data.branch, data.college].filter(Boolean).join(" · ")}</p>
      {data.achievements.length === 0 ? <Empty title="No public achievements" /> :
        <div className="grid gap-4 md:grid-cols-2">{data.achievements.map((a) => <AchievementCard key={a.id} a={a} />)}</div>}
    </div>
  );
}
