import { nextTick } from "vue";
import { render } from "@testing-library/vue";
import Stats from "../src/components/CrashStats.vue";
import { crashStats, listBuckets } from "../src/api.js";
import { emptyCrashStats, crashStatsData, buckets } from "./fixtures.js";
import "lodash/throttle";

// Mock API calls
jest.mock("../src/api.js");
jest.mock("lodash/throttle", () => jest.fn((fn) => fn));

afterEach(jest.resetAllMocks);

test("empty stats doesn't break", async () => {
  crashStats.mockResolvedValue(emptyCrashStats);

  const { container } = await render(Stats, {
    props: {
      restricted: false,
      providers: [],
      activityRange: 14,
    },
    global: {
      stubs: {
        RouterLink: true, // Stub router-link if used in component
      },
    },
  });

  await nextTick();

  expect(crashStats).toHaveBeenCalledTimes(1);
  expect(crashStats).toHaveBeenCalledWith({
    ignore_toolfilter: "0",
  });
  expect(listBuckets).toHaveBeenCalledTimes(0);
  expect(container.querySelector("tbody tr")).toBeNull();
});

test("stats are shown", async () => {
  crashStats.mockResolvedValue(crashStatsData);
  listBuckets.mockResolvedValue(buckets);

  const { getByText, container } = await render(Stats, {
    props: {
      restricted: false,
      providers: [],
      activityRange: 14,
    },
    global: {
      stubs: {
        RouterLink: true,
      },
    },
  });

  await nextTick();

  expect(crashStats).toHaveBeenCalledTimes(1);
  expect(crashStats).toHaveBeenCalledWith({
    ignore_toolfilter: "0",
  });
  expect(listBuckets).toHaveBeenCalledTimes(1);

  // Wait for async operations
  await nextTick();

  expect(container.querySelectorAll("tbody tr").length).toBe(2);
  getByText("A short description for bucket 1");
  const buttonLink = getByText("1630739");
  expect(buttonLink.getAttribute("href")).toBe(buckets[0].bug_urltemplate);
  expect(buttonLink.getAttribute("target")).toBe("_blank");
  getByText("A short description for bucket 2");
  getByText("Assign an existing bug");
});

test("stats use hash params", async () => {
  crashStats.mockResolvedValue(crashStatsData);
  listBuckets.mockResolvedValue(buckets);

  const { container } = await render(Stats, {
    props: {
      restricted: false,
      providers: [],
      activityRange: 14,
    },
    global: {
      mocks: {
        $route: { path: "/stats", hash: "#sort=id&alltools=1" },
        $router: [],
      },
    },
  });

  await nextTick();

  expect(crashStats).toHaveBeenCalledTimes(1);
  expect(crashStats).toHaveBeenCalledWith({
    ignore_toolfilter: "1",
  });
  expect(listBuckets).toHaveBeenCalledTimes(1);

  await nextTick();

  expect(container.querySelectorAll("tbody tr").length).toBe(2);
});

test("stats are sortable", async () => {
  crashStats.mockResolvedValue(crashStatsData);
  listBuckets.mockResolvedValue(buckets);

  const { container } = await render(Stats, {
    props: {
      restricted: false,
      providers: [],
      activityRange: 14,
    },
    global: {
      stubs: {
        RouterLink: true,
      },
      mocks: {
        $route: { hash: "" },
        $router: {
          currentRoute: {
            hash: "",
          },
        },
      },
    },
  });

  await nextTick();

  expect(crashStats).toHaveBeenCalledTimes(1);
  expect(listBuckets).toHaveBeenCalledTimes(1);

  await nextTick();

  let rows = container.querySelectorAll("tbody tr");
  expect(rows.length).toBe(2);
  expect(rows[0].querySelector("td").textContent).toBe("2");
  expect(rows[1].querySelector("td").textContent).toBe("1");

  // Trigger click on first header
  const headers = container.querySelectorAll("thead th");
  await headers[0].click();

  await nextTick();

  rows = container.querySelectorAll("tbody tr");
  expect(rows.length).toBe(2);
  expect(rows[0].querySelector("td").textContent).toBe("2");
  expect(rows[1].querySelector("td").textContent).toBe("1");

  // Trigger another click
  await headers[0].click();

  await nextTick();

  rows = container.querySelectorAll("tbody tr");
  expect(rows.length).toBe(2);
  expect(rows[0].querySelector("td").textContent).toBe("1");
  expect(rows[1].querySelector("td").textContent).toBe("2");

  // Trigger ctrl+click on second header
  const event = new MouseEvent("click", { ctrlKey: true });
  headers[1].dispatchEvent(event);

  await nextTick();
});
