import { useState } from "react"
import {
  Box,
  Heading,
  Card,
  CardBody,
  Text,
  Badge,
  VStack,
  HStack,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  Input,
  FormControl,
  FormLabel,
  Switch,
  Spinner,
  Flex,
  Alert,
  AlertIcon,
} from "@chakra-ui/react"
import { useJobs } from "../hooks/useApi"
import * as api from "../api/client"

export default function System() {
  const { jobs, loading, refetch } = useJobs(200)

  return (
    <Box>
      <Heading size="lg" mb={6} color="white">
        System
      </Heading>

      <Tabs variant="enclosed" colorScheme="brand">
        <TabList>
          <Tab color="gray.400">API Keys</Tab>
          <Tab color="gray.400">Jobs</Tab>
          <Tab color="gray.400">Audit Log</Tab>
          <Tab color="gray.400">Reindex</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <APIKeysPanel />
          </TabPanel>
          <TabPanel>
            <JobsPanel jobs={jobs} loading={loading} refetch={refetch} />
          </TabPanel>
          <TabPanel>
            <AuditLogPanel />
          </TabPanel>
          <TabPanel>
            <ReindexPanel />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

const SCOPES = [
  "personal",
  "personal_finance",
  "biz_finance",
  "biz_projects",
  "coding_projects",
  "infrastructure",
  "social_media_clients",
  "admin",
]

function APIKeysPanel() {
  const [keys, setKeys] = useState<api.APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState("")
  const [scopes, setScopes] = useState<string[]>(["coding_projects"])
  const [canRead, setCanRead] = useState(true)
  const [canWrite, setCanWrite] = useState(true)
  const [newKey, setNewKey] = useState<string | null>(null)

  useState(() => {
    api.getAPIKeys().then(setKeys).finally(() => setLoading(false))
  })

  const handleCreate = async () => {
    if (!name.trim()) return
    try {
      const result = await api.createAPIKey({
        name: name.trim(),
        allowed_scopes: scopes,
        can_read: canRead,
        can_write: canWrite,
      })
      setNewKey((result as Record<string, string>).plain_key || "Key created")
      setName("")
      const updated = await api.getAPIKeys()
      setKeys(updated)
    } catch (e) {
      alert(`Failed: ${e}`)
    }
  }

  const handleRevoke = async (id: string) => {
    if (!confirm("Revoke this key? It cannot be undone.")) return
    try {
      await api.revokeAPIKey(id)
      const updated = await api.getAPIKeys()
      setKeys(updated)
    } catch (e) {
      alert(`Failed: ${e}`)
    }
  }

  if (loading)
    return (
      <Flex justify="center" py={10}>
        <Spinner color="brand.500" />
      </Flex>
    )

  return (
    <Box>
      {newKey && (
        <Alert status="warning" mb={4} borderRadius="lg">
          <AlertIcon />
          <Box>
            <Text fontSize="sm" color="white" fontWeight="bold">
              Copy this key now — it won't be shown again!
            </Text>
            <Text fontFamily="mono" fontSize="sm" color="white" bg="surface.4" p={2} borderRadius="md" mt={1}>
              {newKey}
            </Text>
          </Box>
        </Alert>
      )}

      <Card bg="surface.2" variant="outline" borderColor="surface.3" mb={6}>
        <CardBody>
          <Heading size="sm" mb={4} color="white">
            Create API Key
          </Heading>
          <HStack spacing={4} mb={4}>
            <FormControl flex={1}>
              <FormLabel color="gray.400" fontSize="sm">
                Name
              </FormLabel>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., opencode-client"
                bg="surface.4"
                color="white"
                border="1px solid"
                borderColor="surface.4"
              />
            </FormControl>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Read
              </FormLabel>
              <Switch isChecked={canRead} onChange={(e) => setCanRead(e.target.checked)} colorScheme="green" />
            </FormControl>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Write
              </FormLabel>
              <Switch isChecked={canWrite} onChange={(e) => setCanWrite(e.target.checked)} colorScheme="green" />
            </FormControl>
          </HStack>
          <HStack spacing={2} mb={4} flexWrap="wrap">
            {SCOPES.map((s) => (
              <Button
                key={s}
                size="xs"
                variant={scopes.includes(s) ? "solid" : "outline"}
                colorScheme={scopes.includes(s) ? "brand" : "gray"}
                onClick={() => {
                  setScopes((prev) =>
                    prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]
                  )
                }}
              >
                {s}
              </Button>
            ))}
          </HStack>
          <Button colorScheme="brand" onClick={handleCreate} isDisabled={!name.trim()}>
            Create Key
          </Button>
        </CardBody>
      </Card>

      <VStack spacing={2} align="stretch">
        {keys.map((key) => (
          <Card key={key.id} bg="surface.2" variant="outline" borderColor="surface.3">
            <CardBody py={3}>
              <Flex justify="space-between" align="center">
                <Box>
                  <HStack spacing={2}>
                    <Text fontWeight="semibold" color="white" fontSize="sm">
                      {key.name}
                    </Text>
                    <Badge colorScheme={key.active ? "green" : "red"} fontSize="2xs">
                      {key.active ? "active" : "revoked"}
                    </Badge>
                    <Text fontSize="2xs" color="gray.500">
                      {key.can_read ? "R" : ""}{key.can_write ? "W" : ""}
                    </Text>
                  </HStack>
                  <HStack spacing={1} mt={1}>
                    {key.allowed_scopes.map((s) => (
                      <Badge key={s} colorScheme="cyan" fontSize="2xs">
                        {s}
                      </Badge>
                    ))}
                  </HStack>
                </Box>
                <HStack>
                  <Text fontSize="2xs" color="gray.600">
                    Last: {key.last_used_at?.slice(0, 10) || "never"}
                  </Text>
                  {key.active && (
                    <Button size="xs" colorScheme="red" variant="outline" onClick={() => handleRevoke(key.id)}>
                      Revoke
                    </Button>
                  )}
                </HStack>
              </Flex>
            </CardBody>
          </Card>
        ))}
      </VStack>
    </Box>
  )
}

function JobsPanel({
  jobs,
  loading,
  refetch,
}: {
  jobs: api.IngestionJob[]
  loading: boolean
  refetch: () => void
}) {
  const statusIcon: Record<string, string> = {
    pending: "⏳",
    running: "🔄",
    completed: "✅",
    failed: "❌",
  }

  if (loading)
    return (
      <Flex justify="center" py={10}>
        <Spinner color="brand.500" />
      </Flex>
    )

  return (
    <Box>
      <Text color="gray.400" fontSize="sm" mb={3}>
        {jobs.length} total jobs
      </Text>
      <Table variant="simple" size="sm" colorScheme="whiteAlpha">
        <Thead>
          <Tr>
            <Th color="gray.400">Status</Th>
            <Th color="gray.400">Type</Th>
            <Th color="gray.400">Memory</Th>
            <Th color="gray.400">Attempts</Th>
            <Th color="gray.400">Error</Th>
            <Th color="gray.400">Created</Th>
            <Th color="gray.400">Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {jobs.slice(0, 100).map((job) => (
            <Tr key={job.id}>
              <Td>
                {statusIcon[job.status] || "•"} {job.status}
              </Td>
              <Td color="gray.300" fontSize="xs">
                {job.job_type}
              </Td>
              <Td color="gray.500" fontSize="xs" fontFamily="mono">
                {job.memory_id?.slice(0, 8) || "—"}
              </Td>
              <Td color="gray.400" fontSize="xs">
                {job.attempt_count}
              </Td>
              <Td color="red.400" fontSize="xs" maxW="200px" isTruncated>
                {job.last_error || "—"}
              </Td>
              <Td color="gray.500" fontSize="xs">
                {job.created_at?.slice(0, 16)}
              </Td>
              <Td>
                {(job.status === "failed" || job.status === "pending") && (
                  <Button
                    size="xs"
                    colorScheme="yellow"
                    variant="outline"
                    onClick={async () => {
                      await api.retryJob(job.id)
                      refetch()
                    }}
                  >
                    Retry
                  </Button>
                )}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  )
}

function AuditLogPanel() {
  const [logs, setLogs] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)

  useState(() => {
    api
      .getAuditLogs({ limit: 200 })
      .then(setLogs)
      .finally(() => setLoading(false))
  })

  if (loading)
    return (
      <Flex justify="center" py={10}>
        <Spinner color="brand.500" />
      </Flex>
    )

  return (
    <Table variant="simple" size="sm" colorScheme="whiteAlpha">
      <Thead>
        <Tr>
          <Th color="gray.400">Time</Th>
          <Th color="gray.400">Action</Th>
          <Th color="gray.400">Route</Th>
          <Th color="gray.400">API Key</Th>
        </Tr>
      </Thead>
      <Tbody>
        {logs.map((log, i) => (
          <Tr key={i}>
            <Td color="gray.500" fontSize="xs">
              {String(log.created_at || "").slice(0, 19)}
            </Td>
            <Td color="gray.300" fontSize="xs">
              {String(log.action || "")}
            </Td>
            <Td color="gray.400" fontSize="xs" maxW="250px" isTruncated>
              {String(log.route || "")}
            </Td>
            <Td color="gray.600" fontSize="xs" fontFamily="mono">
              {log.api_key_id ? String(log.api_key_id).slice(0, 8) + "..." : "—"}
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  )
}

function ReindexPanel() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleReindex = async (force: boolean) => {
    setLoading(true)
    setResult(null)
    try {
      const data = await api.reindex({ force })
      setResult(`Queued: ${data.queued}, Skipped: ${data.skipped_no_content}`)
    } catch (e) {
      setResult(`Error: ${e}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Text color="gray.400" mb={4}>
        Reindex all memories to regenerate embeddings. Use force=true to rebuild even if chunks already exist.
      </Text>
      <HStack spacing={3}>
        <Button colorScheme="brand" onClick={() => handleReindex(false)} isLoading={loading}>
          Reindex (missing only)
        </Button>
        <Button colorScheme="orange" onClick={() => handleReindex(true)} isLoading={loading}>
          Force Reindex (all)
        </Button>
      </HStack>
      {result && (
        <Text color="gray.300" mt={4} fontSize="sm">
          {result}
        </Text>
      )}
    </Box>
  )
}