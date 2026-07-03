// Package goqueue provides thread-safe generic queue implementations for Go.
//
// Three types are available:
//
//   - Queue[T]         — simple FIFO queue (not thread-safe)
//   - SafeQueue[T]     — mutex-protected FIFO queue
//   - PriorityQueue[T] — min-heap priority queue
package goqueue

import (
	"container/heap"
	"errors"
	"sync"
)

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

// ErrEmptyQueue is returned when Dequeue or Peek is called on an empty queue.
var ErrEmptyQueue = errors.New("goqueue: queue is empty")

// ---------------------------------------------------------------------------
// Queue — simple generic FIFO queue
// ---------------------------------------------------------------------------

// Queue is a generic first-in, first-out data structure.
// It is NOT safe for concurrent use; see SafeQueue for a thread-safe variant.
type Queue[T any] struct {
	items []T
}

// Enqueue adds item to the back of the queue.
func (q *Queue[T]) Enqueue(item T) {
	q.items = append(q.items, item)
}

// Dequeue removes and returns the front item.
// Returns ErrEmptyQueue if the queue is empty.
func (q *Queue[T]) Dequeue() (T, error) {
	if len(q.items) == 0 {
		var zero T
		return zero, ErrEmptyQueue
	}
	item := q.items[0]
	q.items = q.items[1:]
	return item, nil
}

// Peek returns the front item without removing it.
// Returns ErrEmptyQueue if the queue is empty.
func (q *Queue[T]) Peek() (T, error) {
	if len(q.items) == 0 {
		var zero T
		return zero, ErrEmptyQueue
	}
	return q.items[0], nil
}

// Len returns the number of items in the queue.
func (q *Queue[T]) Len() int { return len(q.items) }

// IsEmpty returns true when the queue contains no items.
func (q *Queue[T]) IsEmpty() bool { return len(q.items) == 0 }

// Clear removes all items from the queue.
func (q *Queue[T]) Clear() { q.items = q.items[:0] }

// ---------------------------------------------------------------------------
// SafeQueue — mutex-protected FIFO queue
// ---------------------------------------------------------------------------

// SafeQueue is a thread-safe generic FIFO queue.
type SafeQueue[T any] struct {
	mu    sync.Mutex
	inner Queue[T]
}

// Enqueue adds item to the back of the queue (thread-safe).
func (sq *SafeQueue[T]) Enqueue(item T) {
	sq.mu.Lock()
	defer sq.mu.Unlock()
	sq.inner.Enqueue(item)
}

// Dequeue removes and returns the front item (thread-safe).
func (sq *SafeQueue[T]) Dequeue() (T, error) {
	sq.mu.Lock()
	defer sq.mu.Unlock()
	return sq.inner.Dequeue()
}

// Peek returns the front item without removing it (thread-safe).
func (sq *SafeQueue[T]) Peek() (T, error) {
	sq.mu.Lock()
	defer sq.mu.Unlock()
	return sq.inner.Peek()
}

// Len returns the current queue length (thread-safe).
func (sq *SafeQueue[T]) Len() int {
	sq.mu.Lock()
	defer sq.mu.Unlock()
	return sq.inner.Len()
}

// IsEmpty returns true when the queue is empty (thread-safe).
func (sq *SafeQueue[T]) IsEmpty() bool {
	sq.mu.Lock()
	defer sq.mu.Unlock()
	return sq.inner.IsEmpty()
}

// ---------------------------------------------------------------------------
// PriorityQueue — min-heap backed priority queue
// ---------------------------------------------------------------------------

// PriorityItem holds a value and its associated priority.
// Lower priority values are dequeued first (min-heap semantics).
type PriorityItem[T any] struct {
	Value    T
	Priority int
	index    int // maintained by heap.Interface
}

type priorityHeap[T any] []*PriorityItem[T]

func (h priorityHeap[T]) Len() int            { return len(h) }
func (h priorityHeap[T]) Less(i, j int) bool  { return h[i].Priority < h[j].Priority }
func (h priorityHeap[T]) Swap(i, j int) {
	h[i], h[j] = h[j], h[i]
	h[i].index = i
	h[j].index = j
}
func (h *priorityHeap[T]) Push(x any) {
	item := x.(*PriorityItem[T])
	item.index = len(*h)
	*h = append(*h, item)
}
func (h *priorityHeap[T]) Pop() any {
	old := *h
	n := len(old)
	item := old[n-1]
	old[n-1] = nil
	*h = old[:n-1]
	return item
}

// PriorityQueue is a generic min-heap priority queue.
// It is NOT thread-safe.
type PriorityQueue[T any] struct {
	h priorityHeap[T]
}

// Enqueue adds value with the given priority. Lower priority = dequeued first.
func (pq *PriorityQueue[T]) Enqueue(value T, priority int) {
	item := &PriorityItem[T]{Value: value, Priority: priority}
	heap.Push(&pq.h, item)
}

// Dequeue removes and returns the item with the lowest priority.
func (pq *PriorityQueue[T]) Dequeue() (T, error) {
	if pq.h.Len() == 0 {
		var zero T
		return zero, ErrEmptyQueue
	}
	item := heap.Pop(&pq.h).(*PriorityItem[T])
	return item.Value, nil
}

// Peek returns the item with the lowest priority without removing it.
func (pq *PriorityQueue[T]) Peek() (T, error) {
	if pq.h.Len() == 0 {
		var zero T
		return zero, ErrEmptyQueue
	}
	return pq.h[0].Value, nil
}

// Len returns the number of items in the priority queue.
func (pq *PriorityQueue[T]) Len() int { return pq.h.Len() }

// IsEmpty returns true when the priority queue contains no items.
func (pq *PriorityQueue[T]) IsEmpty() bool { return pq.h.Len() == 0 }
