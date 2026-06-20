// ─── Mock data for TechJob AI frontend ───────────────────────────────────────

// ---------- Jobs ----------
export const MOCK_JOBS = [
  {
    id: '1',
    title: 'Senior ReactJS Developer',
    company: 'TechCorp Vietnam',
    companyLogo: null,
    companyInitial: 'T',
    companyColor: '#4338CA',
    location: 'TP.HCM',
    type: 'Hybrid',
    level: 'Senior',
    salaryMin: 1500,
    salaryMax: 2500,
    salaryCurrency: 'USD',
    salaryDisplay: '$1,500 – $2,500',
    salaryRaw: null,          // null = có lương thật
    aiEstimatedSalary: 2100,
    skills: ['React', 'TypeScript', 'Next.js', 'Redux', 'GraphQL'],
    description: `Chúng tôi đang tìm kiếm một Senior ReactJS Developer tài năng để gia nhập đội ngũ kỹ thuật cốt lõi tại TP.HCM. Bạn sẽ chịu trách nhiệm xây dựng các ứng dụng web front-end hiệu suất cao phục vụ hàng triệu người dùng.

Trong vai trò này, bạn sẽ cộng tác chặt chẽ với product manager, UX/UI designer và backend engineer để mang lại trải nghiệm người dùng liền mạch, hiệu suất cao. Hiểu biết vững về React patterns hiện đại, state management và tối ưu hóa hiệu suất là yêu cầu thiết yếu.`,
    responsibilities: [
      'Thiết kế và phát triển ứng dụng web mạnh mẽ, có khả năng mở rộng với React.js và Next.js.',
      'Dẫn dắt thảo luận kiến trúc và thiết lập best practices cho front-end engineering.',
      'Tối ưu hóa ứng dụng về tốc độ, khả năng truy cập và khả năng mở rộng.',
      'Mentoring các junior developer và tham gia code review.',
      'Cộng tác với cross-functional teams để định nghĩa, thiết kế và ship các tính năng mới.',
    ],
    requiredSkills: ['ReactJS', 'TypeScript', 'Next.js', 'State Management (Redux/Zustand)', '5+ Years Experience'],
    preferredSkills: ['GraphQL', 'Tailwind CSS', 'CI/CD Pipelines', 'Web Vitals Optimization'],
    benefits: ['Lương tháng 13 + Bonus', 'Bảo hiểm sức khoẻ cao cấp', '12 ngày phép / năm', 'Flexible working hours', 'Budget học tập $500/năm'],
    postedDate: '2 ngày trước',
    deadline: '30/08/2025',
    headcount: 2,
    source: 'ITviec',
    sourceUrl: 'https://itviec.com',
    saved: false,
  },
  {
    id: '2',
    title: 'Backend Engineer (Node.js/AWS)',
    company: 'GlobalSoft Data',
    companyLogo: null,
    companyInitial: 'G',
    companyColor: '#10B981',
    location: 'Remote',
    type: 'Full-time',
    level: 'Mid',
    salaryMin: 2000,
    salaryMax: 3500,
    salaryCurrency: 'USD',
    salaryDisplay: '$2,000 – $3,500',
    salaryRaw: null,
    aiEstimatedSalary: 2800,
    skills: ['Node.js', 'AWS', 'PostgreSQL', 'Docker'],
    description: `GlobalSoft Data tìm kiếm Backend Engineer có kinh nghiệm với Node.js và hệ sinh thái AWS để xây dựng và duy trì các microservices scalable, APIs với hiệu suất cao và độ tin cậy tuyệt vời.`,
    responsibilities: [
      'Xây dựng và duy trì RESTful / GraphQL APIs với Node.js.',
      'Thiết kế và triển khai kiến trúc microservices trên AWS.',
      'Tối ưu hóa database queries và caching strategies.',
      'Viết unit tests, integration tests đạt coverage ≥ 80%.',
    ],
    requiredSkills: ['Node.js', 'AWS (Lambda/ECS/RDS)', 'PostgreSQL', 'Docker', '3+ Years Experience'],
    preferredSkills: ['Kafka', 'Redis', 'Terraform', 'Kubernetes'],
    benefits: ['100% Remote', 'Salary review 2 lần/năm', 'MacBook Pro 14"', 'Co-working space budget'],
    postedDate: '5 ngày trước',
    deadline: '15/09/2025',
    headcount: 1,
    source: 'VietnamWorks',
    sourceUrl: 'https://vietnamworks.com',
    saved: false,
  },
  {
    id: '3',
    title: 'AI Researcher / ML Engineer',
    company: 'NeuroTech Labs',
    companyLogo: null,
    companyInitial: 'N',
    companyColor: '#7C3AED',
    location: 'Hà Nội',
    type: 'Full-time',
    level: 'Senior',
    salaryMin: null,
    salaryMax: null,
    salaryCurrency: 'USD',
    salaryDisplay: 'Thỏa thuận',
    salaryRaw: 'Thỏa thuận',
    aiEstimatedSalary: 3500,
    skills: ['Python', 'PyTorch', 'LLMs', 'TensorFlow'],
    description: `NeuroTech Labs nghiên cứu và phát triển các mô hình AI/ML tiên tiến. Chúng tôi cần AI Researcher/ML Engineer để dẫn đầu các dự án liên quan đến LLMs, computer vision và NLP ứng dụng trong sản phẩm thực tế.`,
    responsibilities: [
      'Nghiên cứu và triển khai các mô hình deep learning mới nhất.',
      'Fine-tuning và deployment LLMs cho các use-case cụ thể.',
      'Xây dựng data pipeline và MLOps workflow.',
      'Publish research papers và present tại các hội nghị quốc tế.',
    ],
    requiredSkills: ['Python', 'PyTorch / TensorFlow', 'LLM Fine-tuning', 'MLOps', 'Research background'],
    preferredSkills: ['Hugging Face', 'RLHF', 'Distributed Training', 'Triton Inference'],
    benefits: ['Research budget không giới hạn', 'Conference attendance', 'PhD sponsorship', 'Stock options'],
    postedDate: '1 tuần trước',
    deadline: '01/10/2025',
    headcount: 3,
    source: 'ITviec',
    sourceUrl: 'https://itviec.com',
    saved: true,
  },
  {
    id: '4',
    title: 'Lead Frontend Engineer',
    company: 'GlobalTech',
    companyLogo: null,
    companyInitial: 'G',
    companyColor: '#6366F1',
    location: 'Remote',
    type: 'Hybrid',
    level: 'Lead',
    salaryMin: 2000,
    salaryMax: 3000,
    salaryCurrency: 'USD',
    salaryDisplay: '$2,000 – $3,000',
    salaryRaw: null,
    aiEstimatedSalary: 2700,
    skills: ['React', 'Vue', 'TypeScript', 'Architecture'],
    description: `Dẫn dắt đội ngũ frontend và định hướng kiến trúc cho hệ thống SaaS B2B quy mô lớn với 500K+ active users.`,
    responsibilities: [
      'Định hướng kỹ thuật cho đội frontend 8 người.',
      'Thiết kế hệ thống component library nội bộ.',
      'Làm việc với CTO để roadmap technical.',
    ],
    requiredSkills: ['React/Vue', 'TypeScript', 'Frontend Architecture', 'Team Leadership'],
    preferredSkills: ['Design Systems', 'Micro-frontend', 'Web Performance'],
    benefits: ['Leadership bonus', 'Equity package', 'Flexible hours', 'Annual retreat'],
    postedDate: '2 ngày trước',
    deadline: '01/09/2025',
    headcount: 1,
    source: 'VietnamWorks',
    sourceUrl: 'https://vietnamworks.com',
    saved: false,
  },
  {
    id: '5',
    title: 'Senior React Developer',
    company: 'InnovateTech VN',
    companyLogo: null,
    companyInitial: 'I',
    companyColor: '#EC4899',
    location: 'Remote',
    type: 'Remote',
    level: 'Senior',
    salaryMin: null,
    salaryMax: 2800,
    salaryCurrency: 'USD',
    salaryDisplay: 'Up to $2,800',
    salaryRaw: null,
    aiEstimatedSalary: 2400,
    skills: ['React', 'Redux', 'Jest', 'Storybook'],
    description: `Phát triển và duy trì các sản phẩm SaaS phục vụ khách hàng doanh nghiệp tại EU và US market. Remote-first culture.`,
    responsibilities: [
      'Phát triển tính năng mới trên React SPA.',
      'Xây dựng và duy trì test suite với Jest/RTL.',
      'Code review và mentoring junior devs.',
    ],
    requiredSkills: ['React 18', 'Redux Toolkit', 'Jest/RTL', 'REST API integration'],
    preferredSkills: ['Storybook', 'Chromatic', 'Playwright'],
    benefits: ['100% Remote', 'USD salary', '25 days PTO', 'Home office budget'],
    postedDate: '5 ngày trước',
    deadline: '20/09/2025',
    headcount: 2,
    source: 'ITviec',
    sourceUrl: 'https://itviec.com',
    saved: false,
  },
  {
    id: '6',
    title: 'Frontend Tech Lead',
    company: 'DataSys Studio',
    companyLogo: null,
    companyInitial: 'D',
    companyColor: '#F59E0B',
    location: 'TP.HCM',
    type: 'On-site',
    level: 'Lead',
    salaryMin: 2500,
    salaryMax: 3500,
    salaryCurrency: 'USD',
    salaryDisplay: '$2,500 – $3,500',
    salaryRaw: null,
    aiEstimatedSalary: 3000,
    skills: ['React', 'Node.js', 'Architecture', 'Mentoring'],
    description: `Lãnh đạo kỹ thuật cho sản phẩm data analytics platform phục vụ 200+ enterprise clients tại Đông Nam Á.`,
    responsibilities: [
      'Kiến trúc toàn bộ frontend stack.',
      'Phỏng vấn và onboarding engineer mới.',
      'Liên lạc với Product và Design teams.',
    ],
    requiredSkills: ['React', 'Node.js', 'Leadership', 'System Design', '7+ Years'],
    preferredSkills: ['WebGL', 'D3.js', 'WebAssembly'],
    benefits: ['Parking', 'Canteen miễn phí', 'Stock options', 'MacBook'],
    postedDate: '1 tuần trước',
    deadline: '15/09/2025',
    headcount: 1,
    source: 'VietnamWorks',
    sourceUrl: 'https://vietnamworks.com',
    saved: false,
  },
]

// ---------- Dashboard charts ----------
export const SKILL_DATA = [
  { skill: 'ReactJS',    jobs: 1245, pct: 15, color: '#4338CA' },
  { skill: 'Java',       jobs: 1120, pct: 13, color: '#5B21B6' },
  { skill: 'Python',     jobs: 980,  pct: 11, color: '#7C3AED' },
  { skill: 'Node.JS',    jobs: 850,  pct: 10, color: '#6366F1' },
  { skill: 'AWS',        jobs: 720,  pct: 8,  color: '#8B5CF6' },
  { skill: 'TypeScript', jobs: 680,  pct: 8,  color: '#A78BFA' },
  { skill: 'Docker',     jobs: 610,  pct: 7,  color: '#C4B5FD' },
  { skill: 'Flutter',    jobs: 540,  pct: 6,  color: '#10B981' },
  { skill: 'Go',         jobs: 480,  pct: 5,  color: '#059669' },
  { skill: 'Kubernetes', jobs: 410,  pct: 5,  color: '#34D399' },
]

export const SALARY_BOX_DATA = [
  { level: 'JUNIOR', min: 400,  q1: 600,  median: 800,  q3: 1000, max: 1400 },
  { level: 'MID',    min: 900,  q1: 1200, median: 1600, q3: 2000, max: 2800 },
  { level: 'SENIOR', min: 1500, q1: 2000, median: 2600, q3: 3200, max: 4500 },
]

export const TREND_DATA_3M = [
  { month: 'Tháng 4', jobs: 820,  salary: 1400, demand: 65 },
  { month: 'Tháng 5', jobs: 950,  salary: 1480, demand: 72 },
  { month: 'Tháng 6', jobs: 1100, salary: 1560, demand: 88 },
]

export const TREND_DATA_6M = [
  { month: 'Tháng 1', jobs: 680,  salary: 1300, demand: 52 },
  { month: 'Tháng 2', jobs: 720,  salary: 1340, demand: 58 },
  { month: 'Tháng 3', jobs: 790,  salary: 1380, demand: 62 },
  { month: 'Tháng 4', jobs: 820,  salary: 1400, demand: 65 },
  { month: 'Tháng 5', jobs: 950,  salary: 1480, demand: 72 },
  { month: 'Tháng 6', jobs: 1100, salary: 1560, demand: 88 },
]

export const TREND_DATA_12M = [
  { month: 'T7/24',   jobs: 540,  salary: 1180, demand: 41 },
  { month: 'T8/24',   jobs: 570,  salary: 1200, demand: 43 },
  { month: 'T9/24',   jobs: 590,  salary: 1220, demand: 46 },
  { month: 'T10/24',  jobs: 610,  salary: 1250, demand: 49 },
  { month: 'T11/24',  jobs: 640,  salary: 1280, demand: 52 },
  { month: 'T12/24',  jobs: 600,  salary: 1260, demand: 48 },
  { month: 'Tháng 1', jobs: 680,  salary: 1300, demand: 52 },
  { month: 'Tháng 2', jobs: 720,  salary: 1340, demand: 58 },
  { month: 'Tháng 3', jobs: 790,  salary: 1380, demand: 62 },
  { month: 'Tháng 4', jobs: 820,  salary: 1400, demand: 65 },
  { month: 'Tháng 5', jobs: 950,  salary: 1480, demand: 72 },
  { month: 'Tháng 6', jobs: 1100, salary: 1560, demand: 88 },
]

// ---------- Market Insights ----------
export const MARKET_SALARY_DATA = [
  { stack: 'ReactJS / Front-end', junior: 700,  mid: 1400, senior: 2600 },
  { stack: 'Node.js / Back-end',  junior: 750,  mid: 1500, senior: 2800 },
  { stack: 'Python / Data & AI',  junior: 800,  mid: 1800, senior: 3500 },
  { stack: 'Java / Enterprise',   junior: 700,  mid: 1500, senior: 3000 },
]

export const EMERGING_SKILLS = [
  { id: 'ai',     label: 'AI',  name: 'Generative AI / LLMs',   growth: '+312%', desc: 'Based on job mentions YoY',   color: '#10B981' },
  { id: 'go',     label: 'GO',  name: 'Golang',                  growth: '+45%',  desc: 'Microservices demand',         color: '#6366F1' },
  { id: 'ops',    label: 'Ops', name: 'DevSecOps',               growth: '+28%',  desc: 'Cloud security focus',         color: '#F59E0B' },
]

// ---------- Chat messages ----------
export const INITIAL_MESSAGES = [
  {
    id: 'sys-1',
    role: 'assistant',
    type: 'text',
    content: 'Xin chào! Tôi là **TechJob AI Assistant** 👋\n\nTôi có thể giúp bạn:\n- 🔍 Tìm việc làm IT phù hợp\n- 📊 Phân tích xu hướng thị trường\n- 💰 So sánh mức lương theo kỹ năng\n- ✍️ Viết Cover Letter chuyên nghiệp\n\nHãy nhập yêu cầu của bạn hoặc chọn một gợi ý bên dưới!',
    timestamp: new Date(Date.now() - 60000),
  }
]

export const QUICK_ACTIONS = [
  { id: 'cover', label: '✍️ Viết Cover Letter',     prompt: 'Hãy giúp tôi viết cover letter cho vị trí ReactJS Developer Senior tại công ty fintech' },
  { id: 'skill', label: '📊 Phân tích kỹ năng',    prompt: 'Phân tích kỹ năng nào đang hot nhất trên thị trường IT Việt Nam hiện tại?' },
  { id: 'salary',label: '💰 So sánh lương',         prompt: 'So sánh mức lương ReactJS vs Python vs Go cho level Senior tại TP.HCM' },
  { id: 'trend', label: '📈 Xu hướng thị trường',   prompt: 'Xu hướng tuyển dụng IT tháng 6/2025 có gì đáng chú ý không?' },
]

// ---------- Profile ----------
export const MOCK_PROFILE = {
  name: 'Nguyễn Văn A',
  title: 'Senior Frontend Developer',
  email: 'nguyenvana@example.com',
  phone: '+84 123 456 789',
  location: 'Ho Chi Minh City, VN',
  nationality: 'Vietnamese',
  gender: 'Male',
  dob: '15 Oct 1990',
  about: 'Passionate Frontend Developer with 5+ years of experience building scalable web applications. Specialized in React, TypeScript, and modern CSS frameworks. Driven by creating intuitive user experiences and writing clean, maintainable code. Actively exploring AI integration in modern UI development.',
  completeness: 85,
  completenessHint: "Add 'Career Preferences' to reach 100%",
  skills: [
    { name: 'ReactJS',    level: 'Expert' },
    { name: 'TypeScript', level: 'Expert' },
    { name: 'Node.js',    level: 'Advanced' },
    { name: 'Python',     level: 'Intermediate' },
    { name: 'AWS',        level: 'Intermediate' },
    { name: 'Docker',     level: 'Beginner' },
  ],
  preferences: {
    position: 'Senior Frontend Developer',
    salaryMin: 2000,
    salaryMax: 3500,
    locations: ['TP.HCM', 'Remote'],
    workTypes: ['Full-time', 'Remote'],
  },
}

export const SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
export const LEVEL_COLOR = {
  Beginner:     'bg-gray-100 text-gray-600',
  Intermediate: 'bg-blue-100 text-blue-700',
  Advanced:     'bg-violet-bg text-violet',
  Expert:       'bg-mint-bg text-mint-dark',
}

// ---------- Filters ----------
export const LOCATIONS   = ['TP.HCM', 'Hà Nội', 'Đà Nẵng', 'Remote']
export const JOB_LEVELS  = ['Junior', 'Mid-Level', 'Senior', 'Lead']
export const WORK_TYPES  = ['Full-time', 'Part-time', 'Remote', 'Hybrid', 'On-site']
export const SALARY_RANGES = [
  { label: 'Tất cả',          min: 0,    max: 99999 },
  { label: '$500 – $1,000',   min: 500,  max: 1000 },
  { label: '$1,000 – $2,000', min: 1000, max: 2000 },
  { label: '$2,000 – $3,500', min: 2000, max: 3500 },
  { label: '$3,500+',         min: 3500, max: 99999 },
]
