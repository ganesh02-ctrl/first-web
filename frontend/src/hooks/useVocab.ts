import { get } from "../services/api";
import type { Vocab } from "../types";
import { useApi } from "./useApi";

let cache: Vocab | null = null;
export function useVocab() {
  return useApi<Vocab>(async () => (cache = cache || (await get<Vocab>("/public/meta"))), []).data;
}
