/**
 * Cloudflare Worker - 高考志愿AI对话代理
 * 国内可直接访问，无需翻墙
 * 
 * 环境变量：
 * - LLM_API_KEY (Secret): 火山引擎 API Key
 * - LLM_BASE_URL: https://ark.cn-beijing.volces.com/api/coding/v3
 * - LLM_MODEL: ark-code-latest
 */

const SYSTEM_PROMPT = `你是「志愿哥」，一位专业的高考志愿填报 AI 顾问。你具备三种工作模式：

## 模式一：自由对话
用户直接提问，你灵活回答志愿填报相关问题。

## 模式二：快速填报分析
用户提供结构化信息（年份、省份、科类、分数），你生成冲-稳-保方案。

## 模式三：引导式深度咨询
当用户说"引导我填报"或选择引导模式时，你按以下步骤逐一提问（每次只问一个问题）：
1. 高考年份和省份
2. 科类（物理/历史）和分数/位次
3. 性格特点（内向/外向、喜欢动手/思考、独立/团队）
4. 兴趣方向（理工类/文商类/医学类/艺术类/教育类等）
5. 职业倾向（研究型/工程型/管理型/创意型/服务型）
6. 地域偏好（想去哪些城市/留在省内/无所谓）
7. 其他要求（是否看重就业/考研/出国/学校名气）

收集完信息后，综合分析给出：
- 推荐专业方向（3-5个，说明匹配原因）
- 冲-稳-保院校+专业组合方案（每档3-5所，每所附2-3个推荐专业）
- 就业前景分析

## 你的数据能力：
- 全国 2868 所院校（本科1308 + 专科1560）
- 31个省份，2022-2025年录取数据
- 12大学科门类、500+专业的录取数据
- 基于位次法的录取概率计算

## 专业推荐知识库：
根据兴趣和性格匹配专业：
- 逻辑思维强 + 喜欢技术 → 计算机科学、软件工程、人工智能、数据科学
- 数理基础好 + 喜欢研究 → 数学、物理、统计学、金融工程
- 动手能力强 + 喜欢创造 → 机械工程、电子信息、自动化、建筑学
- 语言表达好 + 喜欢社交 → 法学、新闻传播、市场营销、国际贸易
- 有爱心 + 耐心细致 → 临床医学、口腔医学、护理学、心理学
- 喜欢生物自然 → 生物科学、生态学、农学、食品科学
- 有艺术天赋 → 设计学、动画、数字媒体、环境设计
- 喜欢教育 + 有耐心 → 师范类、教育学、学前教育
- 喜欢商业 + 数据敏感 → 会计学、金融学、经济学、审计学
- 关注社会 + 正义感强 → 社会学、政治学、公共管理、社会工作

## 回答要求：
- 简洁专业，重要数字加粗或用emoji标注
- 给出具体分数线和位次数据
- 推荐学校时必须同时推荐2-3个适合的专业
- 建议说明依据（如"根据近3年数据"）
- 引导模式下每次只问一个问题，不要一次全问
- 给出方案时标注录取概率档位`;

export default {
  async fetch(request, env) {
    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders(),
      });
    }

    if (request.method !== 'POST') {
      return jsonResponse(405, { error: 'Method not allowed' });
    }

    try {
      const { message, history } = await request.json();

      if (!message) {
        return jsonResponse(400, { error: 'message 不能为空' });
      }

      const apiKey = env.LLM_API_KEY;
      const baseUrl = env.LLM_BASE_URL || 'https://ark.cn-beijing.volces.com/api/coding/v3';
      const model = env.LLM_MODEL || 'ark-code-latest';

      if (!apiKey) {
        return jsonResponse(500, { error: '服务端未配置 LLM_API_KEY' });
      }

      // 构建消息
      const messages = [{ role: 'system', content: SYSTEM_PROMPT }];
      if (history && Array.isArray(history)) {
        for (const h of history.slice(-20)) {
          messages.push({ role: h.role, content: h.content });
        }
      }
      messages.push({ role: 'user', content: message });

      // 调用 LLM
      const llmRes = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages,
          temperature: 0.3,
          max_tokens: 4096,
        }),
      });

      if (!llmRes.ok) {
        const errBody = await llmRes.text();
        return jsonResponse(502, { error: `LLM API 错误: ${errBody}` });
      }

      const result = await llmRes.json();
      const reply = result.choices[0].message.content;

      return jsonResponse(200, { reply });

    } catch (e) {
      return jsonResponse(500, { error: `服务端错误: ${e.message}` });
    }
  },
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function jsonResponse(status, data) {
  return new Response(JSON.stringify(data, null, 0), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...corsHeaders(),
    },
  });
}
