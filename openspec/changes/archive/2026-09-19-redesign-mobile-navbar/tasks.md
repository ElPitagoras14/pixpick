## 1. BottomNav component

- [x] 1.1 Create `frontend/src/features/navigation/BottomNav.tsx` with three items (Home, Create Album, Albums) using `Home`, `Plus` and `Images` from `lucide-react`, taking the active tab as a prop, and verify it renders without errors when mounted under `/_app`
- [x] 1.2 Style `BottomNav` as a `flex md:hidden` fixed bar with the Plus button elevated (primary color, larger, negative `translate-y` overlapping the bar) and verify visually at a 375px-wide viewport that Home/Albums sit level and Plus overlaps the bar's top edge

## 2. Wire into AppLayout

- [x] 2.1 In `frontend/src/routes/_app/route.tsx`, add `hidden md:flex` to the existing Home/Albums `<nav>` block and verify at >=768px the header still shows Home, Albums, avatar/name and logout exactly as before
- [x] 2.2 Compute the active tab and the swipe-route match in `AppLayout` with `useMatchRoute()` (`/home`, `/albums` with `fuzzy: true`, and `/albums/$albumId/swipe`), render `BottomNav` below `md` except on the swipe route, and verify Home/Albums highlight correctly when navigating between `/home` and `/albums`
- [x] 2.3 Add a `pb-[calc(<bar-height>+env(safe-area-inset-bottom))]` spacer to the content wrapper, applied only below `md`, and verify at 375px width on a long page (e.g. the albums list) that the last row isn't covered by the fixed bar

## 3. Verification

- [x] 3.1 At a 375px-wide viewport, verify the footer nav shows Home/Plus/Albums, the top bar is reduced to avatar+name+logout, and tapping Plus navigates to `/albums/new`
- [x] 3.2 At a 375px-wide viewport, open `/albums/$albumId/swipe` and verify the footer nav is not rendered
- [x] 3.3 At >=768px width, verify the layout is pixel-for-pixel the same as before this change (top nav with Home/Albums, no footer nav rendered anywhere)
- [x] 3.4 Run `pnpm check` in `frontend/` and confirm it passes with no new errors
