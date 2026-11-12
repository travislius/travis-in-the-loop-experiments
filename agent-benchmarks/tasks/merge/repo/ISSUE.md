# Bug report

`merge_intervals()` returns wrong results: unsorted input isn't merged, and touching intervals like [1,3] and [3,5] should merge into [1,5]. Nested intervals ([1,10],[2,3]) also break. Input must not be mutated. Fix it.
