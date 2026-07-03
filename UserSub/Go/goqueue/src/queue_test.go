package goqueue_test

import (
	"sync"
	"testing"

	goqueue "github.com/SGizek/Raiku/UserSub/Go/goqueue/src"
)

// ---------------------------------------------------------------------------
// Queue tests
// ---------------------------------------------------------------------------

func TestQueueBasic(t *testing.T) {
	var q goqueue.Queue[int]

	if !q.IsEmpty() {
		t.Fatal("new queue should be empty")
	}

	q.Enqueue(1)
	q.Enqueue(2)
	q.Enqueue(3)

	if q.Len() != 3 {
		t.Fatalf("expected len 3, got %d", q.Len())
	}

	val, err := q.Peek()
	if err != nil || val != 1 {
		t.Fatalf("peek: expected (1, nil), got (%d, %v)", val, err)
	}

	for _, expected := range []int{1, 2, 3} {
		got, err := q.Dequeue()
		if err != nil {
			t.Fatalf("dequeue error: %v", err)
		}
		if got != expected {
			t.Fatalf("expected %d, got %d", expected, got)
		}
	}

	if !q.IsEmpty() {
		t.Fatal("queue should be empty after draining")
	}

	_, err = q.Dequeue()
	if err != goqueue.ErrEmptyQueue {
		t.Fatalf("expected ErrEmptyQueue, got %v", err)
	}
}

func TestQueueClear(t *testing.T) {
	var q goqueue.Queue[string]
	q.Enqueue("a")
	q.Enqueue("b")
	q.Clear()
	if !q.IsEmpty() {
		t.Fatal("queue should be empty after Clear")
	}
}

// ---------------------------------------------------------------------------
// SafeQueue tests
// ---------------------------------------------------------------------------

func TestSafeQueueConcurrent(t *testing.T) {
	var sq goqueue.SafeQueue[int]
	const goroutines = 50
	const items = 100

	var wg sync.WaitGroup
	wg.Add(goroutines)

	for g := 0; g < goroutines; g++ {
		go func(id int) {
			defer wg.Done()
			for i := 0; i < items; i++ {
				sq.Enqueue(id*items + i)
			}
		}(g)
	}

	wg.Wait()

	if sq.Len() != goroutines*items {
		t.Fatalf("expected %d items, got %d", goroutines*items, sq.Len())
	}
}

// ---------------------------------------------------------------------------
// PriorityQueue tests
// ---------------------------------------------------------------------------

func TestPriorityQueueOrder(t *testing.T) {
	var pq goqueue.PriorityQueue[string]

	pq.Enqueue("low",    10)
	pq.Enqueue("high",   1)
	pq.Enqueue("medium", 5)

	expected := []string{"high", "medium", "low"}
	for _, want := range expected {
		got, err := pq.Dequeue()
		if err != nil {
			t.Fatalf("dequeue error: %v", err)
		}
		if got != want {
			t.Fatalf("expected %q, got %q", want, got)
		}
	}
}
