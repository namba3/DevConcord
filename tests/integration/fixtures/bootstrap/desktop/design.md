# Desktop image browser design input

- Project: Field Image Browser
- Platform: Desktop on Windows and Linux.
- Language/build: Rust and Cargo.
- UI: iced is selected for the first implementation.
- User goal: Browse a large local image collection and identify images that need review.
- Functional needs: Incremental listing, visible loading/empty/error states, selection, and a background thumbnail operation with progress and cancellation.
- Robustness: A corrupt image must not terminate the browsing session. Cancellation must leave collection metadata consistent and clearly report completed work.
- Performance: Collections may contain many thousands of images. Avoid loading all full-resolution image data at once; establish a reproducible benchmark input before setting numeric targets.
- Replaceability: Keep image-indexing and selection use cases testable without iced. No second UI implementation is requested.
- Initial bootstrap scope: Development foundation and minimal core/UI boundary; no full browser feature implementation.
