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
  Button,
  Select,
  Spinner,
  Alert,
  AlertIcon,
  Flex,
  Divider,
} from "@chakra-ui/react"
import { useReviewItems, useMemories } from "../hooks/useApi"
import type { Memory, ReviewItem } from "../api/client"
import * as api from "../api/client"

export default function Review() {
  const { items, loading, refetch } = useReviewItems("pending")
  const { memories, refetch: refetchMemories } = useMemories(true, 500)
  const [section, setSection] = useState<"review" | "scratch">("scratch")
  const [resolving, setResolving] = useState<string | null>(null)

  const scratchMemories = memories.filter((m) => m.status === "scratch")

  const handleResolve = async (itemId: string, action: string) => {
    setResolving(itemId)
    try {
      await api.resolveReviewItem(itemId, action)
      refetch()
    } catch (e) {
      alert(`Failed: ${e}`)
    } finally {
      setResolving(null)
    }
  }

  const handlePromote = async (id: string, status: string) => {
    try {
      await api.updateMemory(id, { status })
      refetchMemories()
    } catch (e) {
      alert(`Failed: ${e}`)
    }
  }

  const handleArchive = async (id: string) => {
    try {
      await api.archiveMemory(id)
      refetchMemories()
    } catch (e) {
      alert(`Failed: ${e}`)
    }
  }

  const handleBatchPromote = async (status: string) => {
    if (!confirm(`Promote ALL ${scratchMemories.length} scratch memories to ${status}?`))
      return
    for (const m of scratchMemories) {
      try {
        await api.updateMemory(m.id, { status })
      } catch {
        // skip failures
      }
    }
    refetchMemories()
  }

  if (loading)
    return (
      <Flex justify="center" pt={20}>
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          Review Queue
        </Heading>
        <HStack>
          <Button
            size="sm"
            variant={section === "scratch" ? "solid" : "outline"}
            colorScheme="brand"
            onClick={() => setSection("scratch")}
          >
            Scratch ({scratchMemories.length})
          </Button>
          <Button
            size="sm"
            variant={section === "review" ? "solid" : "outline"}
            colorScheme="brand"
            onClick={() => setSection("review")}
          >
            Review Items ({items.length})
          </Button>
        </HStack>
      </Flex>

      {section === "scratch" && (
        <>
          {scratchMemories.length > 0 && (
            <HStack spacing={2} mb={4}>
              <Button
                size="sm"
                colorScheme="green"
                variant="outline"
                onClick={() => handleBatchPromote("reviewed")}
              >
                Promote All → Reviewed
              </Button>
              <Button
                size="sm"
                colorScheme="blue"
                variant="outline"
                onClick={() => handleBatchPromote("canonical")}
              >
                Promote All → Canonical
              </Button>
              <Button
                size="sm"
                colorScheme="orange"
                variant="outline"
                onClick={async () => {
                  if (!confirm(`Archive ALL ${scratchMemories.length} scratch memories?`)) return
                  for (const m of scratchMemories) {
                    await api.archiveMemory(m.id).catch(() => {})
                  }
                  refetchMemories()
                }}
              >
                Archive All
              </Button>
            </HStack>
          )}

          {scratchMemories.length === 0 ? (
            <Alert status="success" borderRadius="lg">
              <AlertIcon />
              No scratch memories pending review
            </Alert>
          ) : (
            <VStack spacing={3} align="stretch">
              {scratchMemories.map((m) => (
                <Card
                  key={m.id}
                  bg="surface.2"
                  variant="outline"
                  borderColor="yellow.500"
                  _hover={{ borderColor: "yellow.300" }}
                >
                  <CardBody>
                    <Flex justify="space-between" align="start">
                      <Box flex={1}>
                        <HStack spacing={2} mb={1}>
                          <Badge colorScheme="yellow">scratch</Badge>
                          <Badge colorScheme="purple">{m.type}</Badge>
                          <Badge colorScheme="cyan">{m.scope}</Badge>
                        </HStack>
                        <Text fontWeight="semibold" color="white" fontSize="sm">
                          {m.title || m.id.slice(0, 8)}
                        </Text>
                        <Text fontSize="xs" color="gray.400" noOfLines={2} mt={1}>
                          {m.content}
                        </Text>
                      </Box>
                      <HStack spacing={1}>
                        <Button
                          size="xs"
                          colorScheme="green"
                          onClick={() => handlePromote(m.id, "reviewed")}
                        >
                          ✓ Reviewed
                        </Button>
                        <Button
                          size="xs"
                          colorScheme="blue"
                          onClick={() => handlePromote(m.id, "canonical")}
                        >
                          👑 Canonical
                        </Button>
                        <Button
                          size="xs"
                          colorScheme="gray"
                          onClick={() => handleArchive(m.id)}
                        >
                          Archive
                        </Button>
                      </HStack>
                    </Flex>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          )}
        </>
      )}

      {section === "review" && (
        <>
          {items.length === 0 ? (
            <Alert status="success" borderRadius="lg">
              <AlertIcon />
              No pending review items
            </Alert>
          ) : (
            <VStack spacing={4} align="stretch">
              {items.map((item) => (
                <ReviewCard
                  key={item.id}
                  item={item}
                  resolving={resolving === item.id}
                  onResolve={handleResolve}
                />
              ))}
            </VStack>
          )}
        </>
      )}
    </Box>
  )
}

function ReviewCard({
  item,
  resolving,
  onResolve,
}: {
  item: ReviewItem
  resolving: boolean
  onResolve: (id: string, action: string) => void
}) {
  const [targetMem, setTargetMem] = useState<Memory | null>(null)
  const [candidateMem, setCandidateMem] = useState<Memory | null>(null)

  useState(() => {
    api.getMemory(item.memory_id).then(setTargetMem).catch(() => {})
    if (item.candidate_memory_id)
      api.getMemory(item.candidate_memory_id).then(setCandidateMem).catch(() => {})
  })

  return (
    <Card bg="surface.2" variant="outline" borderColor="orange.500">
      <CardBody>
        <HStack spacing={2} mb={2}>
          <Badge colorScheme="orange">{item.review_type}</Badge>
          <Text fontSize="xs" color="gray.500">
            {item.created_at?.slice(0, 10)}
          </Text>
        </HStack>
        {item.reason && (
          <Text fontSize="sm" color="gray.400" mb={2}>
            {item.reason}
          </Text>
        )}

        {targetMem && candidateMem && (
          <HStack spacing={4} mb={3}>
            <Box flex={1} bg="surface.4" p={3} borderRadius="md">
              <Text fontSize="xs" color="blue.400" mb={1} fontWeight="bold">
                Target
              </Text>
              <Text fontSize="sm" color="white" fontWeight="semibold">
                {targetMem.title || targetMem.id.slice(0, 8)}
              </Text>
              <Text fontSize="xs" color="gray.400" noOfLines={3}>
                {targetMem.content}
              </Text>
            </Box>
            <Box flex={1} bg="surface.4" p={3} borderRadius="md">
              <Text fontSize="xs" color="orange.400" mb={1} fontWeight="bold">
                Candidate
              </Text>
              <Text fontSize="sm" color="white" fontWeight="semibold">
                {candidateMem.title || candidateMem.id.slice(0, 8)}
              </Text>
              <Text fontSize="xs" color="gray.400" noOfLines={3}>
                {candidateMem.content}
              </Text>
            </Box>
          </HStack>
        )}

        <Divider my={2} borderColor="surface.4" />

        <HStack spacing={2}>
          <Button
            size="xs"
            colorScheme="green"
            onClick={() => onResolve(item.id, "keep_both")}
            isLoading={resolving}
          >
            Keep Both
          </Button>
          <Button
            size="xs"
            colorScheme="blue"
            onClick={() => onResolve(item.id, "supersede")}
            isLoading={resolving}
          >
            Supersede
          </Button>
          <Button
            size="xs"
            colorScheme="orange"
            onClick={() => onResolve(item.id, "archive_candidate")}
            isLoading={resolving}
          >
            Archive Candidate
          </Button>
          <Button
            size="xs"
            colorScheme="purple"
            onClick={() => onResolve(item.id, "promote_canonical")}
            isLoading={resolving}
          >
            Promote Canonical
          </Button>
        </HStack>
      </CardBody>
    </Card>
  )
}