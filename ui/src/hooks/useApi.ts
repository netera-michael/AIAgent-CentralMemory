import { useEffect, useState, useCallback } from "react"
import * as api from "../api/client"

export function useHealth() {
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)

  const check = useCallback(async () => {
    try {
      const data = await api.healthCheck()
      setConnected(data?.status === "ok")
    } catch {
      setConnected(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    check()
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [check])

  return { connected, loading, refetch: check }
}

export function useStats() {
  const [stats, setStats] = useState<api.Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getStats()
      setStats(data)
      setError(null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch stats")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { stats, loading, error, refetch: fetch }
}

export function useMemories(includeScratch = false, limit = 500) {
  const [memories, setMemories] = useState<api.Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getMemories({
        limit,
        include_scratch: includeScratch,
      })
      setMemories(data)
      setError(null)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch memories")
    } finally {
      setLoading(false)
    }
  }, [includeScratch, limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { memories, loading, error, refetch: fetch, setMemories }
}

export function useReviewItems(status = "pending") {
  const [items, setItems] = useState<api.ReviewItem[]>([])
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getReviewItems({ status, limit: 100 })
      setItems(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [status])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { items, loading, refetch: fetch }
}

export function useEntities(limit = 200) {
  const [entities, setEntities] = useState<api.Entity[]>([])
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getEntities({ limit })
      setEntities(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { entities, loading, refetch: fetch }
}

export function useJobs(limit = 100) {
  const [jobs, setJobs] = useState<api.IngestionJob[]>([])
  const [loading, setLoading] = useState(true)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getIngestionJobs({ limit })
      setJobs(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { jobs, loading, refetch: fetch }
}