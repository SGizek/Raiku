# javastream

Extended Java Stream combinators and collectors. Requires Java 17+.

## Installation

```bash
raiku install javastream
```

## Usage

```java
import dev.raiku.javastream.StreamUtils;
import java.util.stream.Stream;

// Zip two streams
StreamUtils.zip(Stream.of("a","b"), Stream.of(1, 2), (k,v) -> k+"="+v)
           .forEach(System.out::println);
// a=1  b=2

// Sliding window
StreamUtils.windowed(Stream.of(1,2,3,4,5), 3)
           .forEach(System.out::println);
// [1,2,3]  [2,3,4]  [3,4,5]

// Chunk
StreamUtils.chunk(Stream.of(1,2,3,4,5), 2)
           .forEach(System.out::println);
// [1,2]  [3,4]  [5]
```

## License

MIT
