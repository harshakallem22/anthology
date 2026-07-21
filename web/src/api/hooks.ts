import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import type {
  Article,
  ArticleDetail,
  Highlight,
  ImportJob,
  SearchResults,
  Tag,
  User,
} from "@/lib/types";

export function useMe() {
  return useQuery<User | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        const { data } = await api.get<User>("/auth/me");
        return data;
      } catch {
        return null;
      }
    },
    retry: false,
    staleTime: 60_000,
  });
}

export function useDevLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<User>("/auth/dev-login")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => api.post("/auth/logout"),
    onSuccess: () => qc.setQueryData(["me"], null),
  });
}

export interface ArticleFilters {
  archived?: boolean;
  favorite?: boolean;
  tag?: string;
}

export function useArticles(filters: ArticleFilters = {}) {
  return useQuery<Article[]>({
    queryKey: ["articles", filters],
    queryFn: async () => {
      const params: Record<string, string | boolean> = {
        archived: filters.archived ?? false,
      };
      if (filters.favorite) params.favorite = true;
      if (filters.tag) params.tag = filters.tag;
      const { data } = await api.get<Article[]>("/articles", { params });
      return data;
    },
  });
}

export function useArticle(id: string | undefined) {
  return useQuery<ArticleDetail>({
    queryKey: ["article", id],
    queryFn: async () => (await api.get<ArticleDetail>(`/articles/${id}`)).data,
    enabled: !!id,
  });
}

export function useUpdateArticle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: {
      id: string;
      is_favorite?: boolean;
      is_archived?: boolean;
    }) => {
      const { id, ...body } = vars;
      return (await api.patch<Article>(`/articles/${id}`, body)).data;
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["articles"] });
      qc.invalidateQueries({ queryKey: ["article"] });
    },
  });
}

export function useDeleteArticle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/articles/${id}`),
    onSettled: () => qc.invalidateQueries({ queryKey: ["articles"] }),
  });
}

export function useTags() {
  return useQuery<Tag[]>({
    queryKey: ["tags"],
    queryFn: async () => (await api.get<Tag[]>("/tags")).data,
  });
}

export function useAddTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { articleId: string; name: string }) =>
      (await api.post<Tag[]>(`/articles/${vars.articleId}/tags`, { name: vars.name }))
        .data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["article"] });
      qc.invalidateQueries({ queryKey: ["articles"] });
      qc.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}

export function useRemoveTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { articleId: string; name: string }) =>
      api.delete(`/articles/${vars.articleId}/tags/${encodeURIComponent(vars.name)}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["article"] });
      qc.invalidateQueries({ queryKey: ["articles"] });
    },
  });
}

export function useHighlights(articleId: string | undefined) {
  return useQuery<Highlight[]>({
    queryKey: ["highlights", articleId],
    queryFn: async () =>
      (await api.get<Highlight[]>(`/articles/${articleId}/highlights`)).data,
    enabled: !!articleId,
  });
}

export function useCreateHighlight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: {
      articleId: string;
      quote: string;
      note?: string;
      position?: object;
    }) =>
      (
        await api.post<Highlight>(`/articles/${vars.articleId}/highlights`, {
          quote: vars.quote,
          note: vars.note ?? null,
          position: vars.position ?? null,
        })
      ).data,
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: ["highlights", vars.articleId] }),
  });
}

export function useDeleteHighlight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { id: string; articleId: string }) =>
      api.delete(`/highlights/${vars.id}`),
    onSuccess: (_d, vars) =>
      qc.invalidateQueries({ queryKey: ["highlights", vars.articleId] }),
  });
}

export function useCreateImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { file: File; source?: string }) => {
      const form = new FormData();
      form.append("file", vars.file);
      if (vars.source) form.append("source", vars.source);
      return (
        await api.post<ImportJob>("/imports", form, {
          headers: { "Content-Type": "multipart/form-data" },
        })
      ).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["articles"] }),
  });
}

export function useImportStatus(id: string | undefined, poll: boolean) {
  return useQuery<ImportJob>({
    queryKey: ["import", id],
    queryFn: async () => (await api.get<ImportJob>(`/imports/${id}`)).data,
    enabled: !!id,
    refetchInterval: poll ? 1200 : false,
  });
}

export function useSearch(q: string, tags?: string) {
  return useQuery<SearchResults>({
    queryKey: ["search", q, tags],
    queryFn: async () => {
      const params: Record<string, string> = { q };
      if (tags) params.tags = tags;
      return (await api.get<SearchResults>("/search", { params })).data;
    },
    enabled: q.trim().length > 0,
  });
}
