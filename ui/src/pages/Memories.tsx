import { useState, useMemo } from "react"
import {
  Box,
  Heading,
  Input,
  Select,
  HStack,
  Card,
  CardBody,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  Spinner,
  Alert,
  AlertIcon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useDisclosure,
  VStack,
  FormControl,
  FormLabel,
  Textarea,
  SimpleGrid,
  Flex,
  IconButton,
} from "@chakra-ui/react"
import { FiFilter, FiRefreshCw } from "react-icons/fi"
import { useMemories } from "../hooks/useApi"
import type { Memory } from "../api/client"
import * as api from "../api/client"

const STATUS_COLORS: Record<string, string> = {
  canonical: "blue",
  reviewed: "green",
  scratch: "yellow",
  stale: "gray",
  conflicted: "red",
  archived: "gray",
}

const SCOPES = [
  "personal",
  "personal_finance",
  "biz_finance",
  "biz_projects",
  "coding_projects",
  "infrastructure",
  "social_media_clients",
]

const TYPES = ["fact", "preference", "decision", "workflow", "project_note"]
const STATUSES = ["scratch", "reviewed", "canonical", "stale", "conflicted", "archived"]

export default function Memories() {
  const { memories, loading, error, refetch } = useMemories(true, 500)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  const [scopeFilter, setScopeFilter] = useState<string>("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [page, setPage] = useState(0)
  const pageSize = 25
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selected, setSelected] = useState<Memory | null>(null)

  const filtered = useMemo(() => {
    let result = memories
    if (statusFilter) result = result.filter((m) => m.status === statusFilter)
    if (scopeFilter) result = result.filter((m) => m.scope === scopeFilter)
    if (typeFilter) result = result.filter((m) => m.type === typeFilter)
    if (search) {
      const q = search.toLowerCase()
      result = result.filter(
        (m) =>
          (m.title || "").toLowerCase().includes(q) ||
          m.content.toLowerCase().includes(q) ||
          (m.summary || "").toLowerCase().includes(q)
      )
    }
    return result
  }, [memories, search, statusFilter, scopeFilter, typeFilter])

  const pageData = filtered.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.ceil(filtered.length / pageSize)

  const handleAction = async (action: string, mem: Memory) => {
    try {
      if (action === "archive") await api.archiveMemory(mem.id)
      else if (action === "purge") await api.purgeMemory(mem.id)
      else if (action === "reviewed")
        await api.updateMemory(mem.id, { status: "reviewed" })
      else if (action === "canonical")
        await api.updateMemory(mem.id, { status: "canonical" })
      refetch()
      onClose()
    } catch (e) {
      alert(`Failed: ${e}`)
    }
  }

  if (loading)
    return (
      <Flex justify="center" pt={20}>
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )
  if (error)
    return (
      <Alert status="error">
        <AlertIcon />
        {error}
      </Alert>
    )

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          Memories
        </Heading>
        <IconButton
          icon={<FiRefreshCw />}
          onClick={refetch}
          aria-label="Refresh"
          variant="ghost"
          color="gray.400"
        />
      </Flex>

      <HStack spacing={3} mb={4} flexWrap="wrap">
        <Input
          placeholder="Search title, content, summary..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          maxW="300px"
          bg="navy.700"
          border="1px solid"
          borderColor="whiteAlpha.100"
          color="white"
          _placeholder={{ color: "gray.500" }}
        />
        <Select
          placeholder="Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          maxW="150px"
          bg="navy.700"
          border="1px solid"
          borderColor="whiteAlpha.100"
          color="white"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
        <Select
          placeholder="Scope"
          value={scopeFilter}
          onChange={(e) => setScopeFilter(e.target.value)}
          maxW="180px"
          bg="navy.700"
          border="1px solid"
          borderColor="whiteAlpha.100"
          color="white"
        >
          {SCOPES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
        <Select
          placeholder="Type"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          maxW="150px"
          bg="navy.700"
          border="1px solid"
          borderColor="whiteAlpha.100"
          color="white"
        >
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>
        <Text color="gray.500" fontSize="sm">
          {filtered.length} memories
        </Text>
      </HStack>

      <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100" overflow="hidden">
        <CardBody p={0}>
          <Table variant="simple" size="sm" colorScheme="whiteAlpha">
            <Thead>
              <Tr>
                <Th color="gray.400" borderBottomColor="whiteAlpha.200">
                  Title
                </Th>
                <Th color="gray.400" borderBottomColor="whiteAlpha.200">
                  Type
                </Th>
                <Th color="gray.400" borderBottomColor="whiteAlpha.200">
                  Scope
                </Th>
                <Th color="gray.400" borderBottomColor="whiteAlpha.200">
                  Status
                </Th>
                <Th color="gray.400" borderBottomColor="whiteAlpha.200">
                  Created
                </Th>
              </Tr>
            </Thead>
            <Tbody>
              {pageData.map((m) => (
                <Tr
                  key={m.id}
                  cursor="pointer"
                  _hover={{ bg: "whiteAlpha.50" }}
                  onClick={() => {
                    setSelected(m)
                    onOpen()
                  }}
                >
                  <Td color="white" maxW="250px" isTruncated>
                    {m.title || m.id.slice(0, 8)}
                  </Td>
                  <Td>
                    <Badge colorScheme="purple" fontSize="2xs">
                      {m.type}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme="cyan" fontSize="2xs">
                      {m.scope}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge colorScheme={STATUS_COLORS[m.status] || "gray"} fontSize="2xs">
                      {m.status}
                    </Badge>
                  </Td>
                  <Td color="gray.400" fontSize="xs">
                    {m.created_at?.slice(0, 10)}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </CardBody>
      </Card>

      <Flex justify="space-between" align="center" mt={4}>
        <Text color="gray.500" fontSize="sm">
          Page {page + 1} of {totalPages}
        </Text>
        <HStack>
          <Button
            size="sm"
            variant="ghost"
            color="gray.400"
            onClick={() => setPage(Math.max(0, page - 1))}
            isDisabled={page === 0}
          >
            Previous
          </Button>
          <Button
            size="sm"
            variant="ghost"
            color="gray.400"
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            isDisabled={page >= totalPages - 1}
          >
            Next
          </Button>
        </HStack>
      </Flex>

      {selected && (
        <MemoryModal
          memory={selected}
          isOpen={isOpen}
          onClose={onClose}
          onAction={handleAction}
        />
      )}
    </Box>
  )
}

function MemoryModal({
  memory,
  isOpen,
  onClose,
  onAction,
}: {
  memory: Memory
  isOpen: boolean
  onClose: () => void
  onAction: (action: string, mem: Memory) => void
}) {
  const [editTitle, setEditTitle] = useState(memory.title || "")
  const [editContent, setEditContent] = useState(memory.content)
  const [editSummary, setEditSummary] = useState(memory.summary || "")
  const [editStatus, setEditStatus] = useState(memory.status)

  const handleUpdate = async () => {
    const payload: Partial<Memory> = {}
    if (editTitle !== (memory.title || "")) payload.title = editTitle
    if (editSummary !== (memory.summary || "")) payload.summary = editSummary
    if (editContent !== memory.content) payload.content = editContent
    if (editStatus !== memory.status) payload.status = editStatus
    if (Object.keys(payload).length > 0) {
      await api.updateMemory(memory.id, payload)
    }
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay bg="blackAlpha.700" />
      <ModalContent bg="navy.800" maxH="90vh" overflowY="auto">
        <ModalHeader color="white">
          <HStack spacing={3}>
            <Badge colorScheme={STATUS_COLORS[memory.status] || "gray"}>
              {memory.status}
            </Badge>
            <Badge colorScheme="purple">{memory.type}</Badge>
            <Badge colorScheme="cyan">{memory.scope}</Badge>
          </HStack>
        </ModalHeader>
        <ModalCloseButton color="gray.400" />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <SimpleGrid columns={2} spacing={4}>
              <FormControl>
                <FormLabel color="gray.400" fontSize="sm">
                  ID
                </FormLabel>
                <Text fontSize="xs" color="gray.500" fontFamily="mono">
                  {memory.id}
                </Text>
              </FormControl>
              <FormControl>
                <FormLabel color="gray.400" fontSize="sm">
                  Created
                </FormLabel>
                <Text fontSize="sm" color="gray.300">
                  {memory.created_at}
                </Text>
              </FormControl>
            </SimpleGrid>

            {memory.valid_from && (
              <Box>
                <Text fontSize="xs" color="gray.500">
                  Valid: {memory.valid_from?.slice(0, 10)}
                  {memory.valid_until ? ` → ${memory.valid_until.slice(0, 10)}` : " → now"}
                </Text>
                {memory.supersedes_memory_id && (
                  <Text fontSize="xs" color="blue.400">
                    Supersedes: {memory.supersedes_memory_id.slice(0, 8)}...
                  </Text>
                )}
              </Box>
            )}

            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Title
              </FormLabel>
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                bg="navy.900"
                color="white"
                border="1px solid"
                borderColor="whiteAlpha.200"
              />
            </FormControl>

            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Summary
              </FormLabel>
              <Textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                rows={2}
                bg="navy.900"
                color="white"
                border="1px solid"
                borderColor="whiteAlpha.200"
              />
            </FormControl>

            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Content
              </FormLabel>
              <Textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={8}
                bg="navy.900"
                color="white"
                border="1px solid"
                borderColor="whiteAlpha.200"
                fontFamily="mono"
                fontSize="sm"
              />
            </FormControl>

            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Status
              </FormLabel>
              <Select
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value)}
                bg="navy.900"
                color="white"
                border="1px solid"
                borderColor="whiteAlpha.200"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <HStack spacing={2}>
            <Button size="sm" colorScheme="green" onClick={handleUpdate}>
              Save
            </Button>
            {memory.status === "scratch" && (
              <>
                <Button
                  size="sm"
                  colorScheme="green"
                  variant="outline"
                  onClick={() => onAction("reviewed", memory)}
                >
                  Promote → Reviewed
                </Button>
                <Button
                  size="sm"
                  colorScheme="blue"
                  variant="outline"
                  onClick={() => onAction("canonical", memory)}
                >
                  Promote → Canonical
                </Button>
              </>
            )}
            <Button
              size="sm"
              colorScheme="orange"
              variant="outline"
              onClick={() => onAction("archive", memory)}
            >
              Archive
            </Button>
            <Button
              size="sm"
              colorScheme="red"
              variant="outline"
              onClick={() => {
                if (confirm("Permanently delete this memory?")) onAction("purge", memory)
              }}
            >
              Purge
            </Button>
            <Button size="sm" variant="ghost" color="gray.400" onClick={onClose}>
              Close
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}