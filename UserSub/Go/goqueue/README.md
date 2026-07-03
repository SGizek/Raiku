# goqueue

Thread-safe generic queue implementations for Go 1.21+.

Provides three types:
- `Queue[T]` — simple FIFO (not thread-safe)
- `SafeQueue[T]` — mutex-protected FIFO
- `PriorityQueue[T]` — min-heap priority queue

## Installation

```bash
raiku install goqueue
```

## Usage

```go
import goqueue "github.com/SGizek/Raiku/UserSub/Go/goqueue/src"

// Simple queue
var q goqueue.Queue[int]
q.Enqueue(1)
q.Enqueue(2)
val, _ := q.Dequeue() // 1

// Thread-safe queue
var sq goqueue.SafeQueue[string]
sq.Enqueue("hello")

// Priority queue (lower number = higher priority)
var pq goqueue.PriorityQueue[string]
pq.Enqueue("low", 10)
pq.Enqueue("high", 1)
top, _ := pq.Dequeue() // "high"
```

## License

MIT
