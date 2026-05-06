// Dashboard data for CB2 Collateral and MCSS Clock Connection

const CB2_DATA = {
  summary: {
    totalDeliverables: 24,
    completed: 14,
    inProgress: 7,
    notStarted: 3,
    lastUpdated: "2026-05-06",
  },

  categories: [
    {
      name: "Architecture & Spec",
      items: [
        { id: "AS-01", name: "CB2 Top-Level Architecture Spec", owner: "H. Tanaka", status: "Complete", quality: 98, dueDate: "2026-01-15", completedDate: "2026-01-12" },
        { id: "AS-02", name: "Clock Distribution Network Spec", owner: "M. Patel", status: "Complete", quality: 95, dueDate: "2026-01-30", completedDate: "2026-01-28" },
        { id: "AS-03", name: "Power Domain Partitioning Doc", owner: "S. Kim", status: "Complete", quality: 92, dueDate: "2026-02-10", completedDate: "2026-02-08" },
        { id: "AS-04", name: "Timing Closure Guidelines", owner: "R. Chen", status: "In Progress", quality: 74, dueDate: "2026-05-20", completedDate: null },
      ],
    },
    {
      name: "RTL Design",
      items: [
        { id: "RT-01", name: "Clock Gating Cell Integration", owner: "A. Nguyen", status: "Complete", quality: 96, dueDate: "2026-02-28", completedDate: "2026-02-25" },
        { id: "RT-02", name: "PLL Wrapper RTL", owner: "B. Liu", status: "Complete", quality: 91, dueDate: "2026-03-10", completedDate: "2026-03-07" },
        { id: "RT-03", name: "Clock Mux Network RTL", owner: "C. Wang", status: "In Progress", quality: 82, dueDate: "2026-05-15", completedDate: null },
        { id: "RT-04", name: "Scan Clock Controller RTL", owner: "D. Park", status: "In Progress", quality: 68, dueDate: "2026-05-30", completedDate: null },
        { id: "RT-05", name: "BISR Clock Logic RTL", owner: "E. Gomez", status: "Not Started", quality: 0, dueDate: "2026-06-15", completedDate: null },
      ],
    },
    {
      name: "Verification",
      items: [
        { id: "VR-01", name: "Clock Domain Crossing (CDC) Signoff", owner: "F. Ahmed", status: "Complete", quality: 99, dueDate: "2026-03-20", completedDate: "2026-03-18" },
        { id: "VR-02", name: "UVM Testbench for Clock Mux", owner: "G. Silva", status: "Complete", quality: 94, dueDate: "2026-03-31", completedDate: "2026-03-29" },
        { id: "VR-03", name: "Formal Verification – PLL Wrapper", owner: "H. Kumar", status: "Complete", quality: 97, dueDate: "2026-04-10", completedDate: "2026-04-08" },
        { id: "VR-04", name: "Regression Coverage Report", owner: "I. Zhao", status: "In Progress", quality: 88, dueDate: "2026-05-25", completedDate: null },
        { id: "VR-05", name: "Low Power Simulation Signoff", owner: "J. Lee", status: "In Progress", quality: 61, dueDate: "2026-06-05", completedDate: null },
      ],
    },
    {
      name: "Physical Design",
      items: [
        { id: "PD-01", name: "Floorplan & Clock Tree Budgeting", owner: "K. Müller", status: "Complete", quality: 93, dueDate: "2026-04-01", completedDate: "2026-03-30" },
        { id: "PD-02", name: "CTS – Global Clock Mesh Synthesis", owner: "L. Rossi", status: "Complete", quality: 90, dueDate: "2026-04-20", completedDate: "2026-04-18" },
        { id: "PD-03", name: "CTS – Leaf-Level Buffer Insertion", owner: "M. Brown", status: "In Progress", quality: 77, dueDate: "2026-05-18", completedDate: null },
        { id: "PD-04", name: "DRC / LVS Signoff", owner: "N. White", status: "Not Started", quality: 0, dueDate: "2026-06-20", completedDate: null },
        { id: "PD-05", name: "STA Final Signoff", owner: "O. Black", status: "Not Started", quality: 0, dueDate: "2026-07-01", completedDate: null },
      ],
    },
    {
      name: "Documentation",
      items: [
        { id: "DO-01", name: "Integration Guide (CB2 to SoC)", owner: "P. Green", status: "Complete", quality: 96, dueDate: "2026-04-15", completedDate: "2026-04-14" },
        { id: "DO-02", name: "Collateral Release Package v1.0", owner: "Q. Hall", status: "Complete", quality: 100, dueDate: "2026-04-30", completedDate: "2026-04-28" },
        { id: "DO-03", name: "Known Issues & Errata List", owner: "R. Adams", status: "In Progress", quality: 55, dueDate: "2026-05-20", completedDate: null },
      ],
    },
  ],

  qualityTrend: {
    labels: ["Jan", "Feb", "Mar", "Apr", "May"],
    avgScore: [72, 78, 84, 90, 87],
    defectsFound: [18, 14, 9, 5, 6],
    defectsClosed: [10, 16, 11, 7, 4],
  },
};

const MCSS_DATA = {
  summary: {
    totalConnections: 48,
    passed: 39,
    marginal: 6,
    failed: 3,
    lastUpdated: "2026-05-06",
  },

  connections: [
    // format: id, source domain, target domain, freq_mhz, skew_ps, jitter_ps, duty_cycle_err_pct, status
    { id: "CLK-001", src: "PLL_CORE_A", dst: "CPU_CLUSTER_0", freqMHz: 2000, skewPs: 12, jitterPs: 8, dutyCycleErr: 0.3, status: "Pass" },
    { id: "CLK-002", src: "PLL_CORE_A", dst: "CPU_CLUSTER_1", freqMHz: 2000, skewPs: 15, jitterPs: 9, dutyCycleErr: 0.4, status: "Pass" },
    { id: "CLK-003", src: "PLL_CORE_B", dst: "GPU_CLUSTER_0", freqMHz: 1800, skewPs: 18, jitterPs: 11, dutyCycleErr: 0.5, status: "Pass" },
    { id: "CLK-004", src: "PLL_CORE_B", dst: "GPU_CLUSTER_1", freqMHz: 1800, skewPs: 22, jitterPs: 14, dutyCycleErr: 0.7, status: "Pass" },
    { id: "CLK-005", src: "PLL_MEM",    dst: "LPDDR5_PHY_0",  freqMHz: 3200, skewPs: 8,  jitterPs: 6,  dutyCycleErr: 0.2, status: "Pass" },
    { id: "CLK-006", src: "PLL_MEM",    dst: "LPDDR5_PHY_1",  freqMHz: 3200, skewPs: 10, jitterPs: 7,  dutyCycleErr: 0.3, status: "Pass" },
    { id: "CLK-007", src: "PLL_IO",     dst: "PCIe_5.0_PHY",  freqMHz:  100, skewPs: 25, jitterPs: 18, dutyCycleErr: 1.1, status: "Marginal" },
    { id: "CLK-008", src: "PLL_IO",     dst: "USB4_PHY",       freqMHz:  20,  skewPs: 19, jitterPs: 12, dutyCycleErr: 0.6, status: "Pass" },
    { id: "CLK-009", src: "PLL_MEDIA",  dst: "VPU_CORE",       freqMHz:  900, skewPs: 14, jitterPs: 10, dutyCycleErr: 0.4, status: "Pass" },
    { id: "CLK-010", src: "PLL_MEDIA",  dst: "ISP_CORE",       freqMHz:  700, skewPs: 16, jitterPs: 11, dutyCycleErr: 0.5, status: "Pass" },
    { id: "CLK-011", src: "PLL_AI",     dst: "NPU_CLUSTER_0",  freqMHz: 1200, skewPs: 20, jitterPs: 16, dutyCycleErr: 0.8, status: "Pass" },
    { id: "CLK-012", src: "PLL_AI",     dst: "NPU_CLUSTER_1",  freqMHz: 1200, skewPs: 31, jitterPs: 22, dutyCycleErr: 1.4, status: "Marginal" },
    { id: "CLK-013", src: "REF_25M",    dst: "PLL_CORE_A",     freqMHz:  25,  skewPs: 5,  jitterPs: 3,  dutyCycleErr: 0.1, status: "Pass" },
    { id: "CLK-014", src: "REF_25M",    dst: "PLL_CORE_B",     freqMHz:  25,  skewPs: 5,  jitterPs: 3,  dutyCycleErr: 0.1, status: "Pass" },
    { id: "CLK-015", src: "REF_25M",    dst: "PLL_MEM",        freqMHz:  25,  skewPs: 4,  jitterPs: 3,  dutyCycleErr: 0.1, status: "Pass" },
    { id: "CLK-016", src: "SCAN_CLK",   dst: "CPU_CLUSTER_0",  freqMHz:  200, skewPs: 45, jitterPs: 30, dutyCycleErr: 2.1, status: "Failed" },
    { id: "CLK-017", src: "SCAN_CLK",   dst: "GPU_CLUSTER_0",  freqMHz:  200, skewPs: 52, jitterPs: 35, dutyCycleErr: 2.6, status: "Failed" },
    { id: "CLK-018", src: "PLL_SYS",    dst: "FABRIC_CORE",    freqMHz:  800, skewPs: 11, jitterPs: 8,  dutyCycleErr: 0.3, status: "Pass" },
    { id: "CLK-019", src: "PLL_SYS",    dst: "NOC_ROUTER",     freqMHz:  800, skewPs: 13, jitterPs: 9,  dutyCycleErr: 0.4, status: "Pass" },
    { id: "CLK-020", src: "PLL_PERIPH", dst: "UART_CTRL",      freqMHz:  50,  skewPs: 30, jitterPs: 20, dutyCycleErr: 1.2, status: "Marginal" },
    { id: "CLK-021", src: "PLL_PERIPH", dst: "SPI_CTRL",       freqMHz:  50,  skewPs: 28, jitterPs: 18, dutyCycleErr: 1.0, status: "Pass" },
    { id: "CLK-022", src: "PLL_PERIPH", dst: "I2C_CTRL",       freqMHz:  50,  skewPs: 26, jitterPs: 17, dutyCycleErr: 0.9, status: "Pass" },
    { id: "CLK-023", src: "PLL_SEC",    dst: "CRYPTO_ENGINE",  freqMHz:  400, skewPs: 17, jitterPs: 12, dutyCycleErr: 0.5, status: "Pass" },
    { id: "CLK-024", src: "PLL_SEC",    dst: "SECURE_ENCLAVE", freqMHz:  400, skewPs: 16, jitterPs: 11, dutyCycleErr: 0.4, status: "Pass" },
    { id: "CLK-025", src: "TEST_OSC",   dst: "BIST_CTRL",      freqMHz:  100, skewPs: 55, jitterPs: 40, dutyCycleErr: 3.2, status: "Failed" },
    { id: "CLK-026", src: "PLL_DISP",   dst: "DISPLAY_CTRL",   freqMHz:  594, skewPs: 14, jitterPs: 9,  dutyCycleErr: 0.4, status: "Pass" },
    { id: "CLK-027", src: "PLL_DISP",   dst: "MIPI_DSI_PHY",   freqMHz:  594, skewPs: 18, jitterPs: 12, dutyCycleErr: 0.6, status: "Pass" },
    { id: "CLK-028", src: "PLL_CAM",    dst: "MIPI_CSI_PHY_0", freqMHz:  420, skewPs: 22, jitterPs: 15, dutyCycleErr: 0.7, status: "Pass" },
    { id: "CLK-029", src: "PLL_CAM",    dst: "MIPI_CSI_PHY_1", freqMHz:  420, skewPs: 23, jitterPs: 16, dutyCycleErr: 0.7, status: "Marginal" },
    { id: "CLK-030", src: "PLL_CAM",    dst: "ISP_CORE",       freqMHz:  420, skewPs: 21, jitterPs: 14, dutyCycleErr: 0.6, status: "Pass" },
  ],

  qualityMetrics: {
    labels: ["Jan", "Feb", "Mar", "Apr", "May"],
    passRate:     [72, 78, 83, 87, 81],
    avgSkewPs:    [38, 31, 26, 20, 22],
    avgJitterPs:  [26, 21, 18, 13, 15],
  },

  skewDistribution: {
    bins:   ["0–10", "11–20", "21–30", "31–40", "41–55", ">55"],
    counts: [5, 10, 9, 3, 2, 1],
  },
};
