"""
All prompt templates for Insight Copilot.
Keep prompts here, not scattered in node files.
Changing a prompt = changing only this file.
"""

INTENT_ROUTER_PROMPT = """You are classifying a business
user's question to decide how to answer it.

Available data sources:
- Structured data file (CSV/Excel) uploaded: {has_csv}
- Business document (PDF) uploaded: {has_pdf}

User question: "{question}"

Classification rules:

"analytics" — question is ONLY about numbers, metrics,
trends, rankings, or patterns in the structured data.
No mention of documents, reports, or text content.
Examples:
  "which ship mode drives the most revenue?"
  "show me sales by category"
  "what are the top 5 products?"
  "are there any anomalies in sales?"
  "which region is underperforming?"

"rag" — question is ONLY about what a document says.
No mention of data, numbers, or metrics.
Examples:
  "what does the report say?"
  "summarise the document"
  "what recommendations are in the PDF?"
  "what risks are mentioned in the report?"

"both" — question asks about BOTH the structured data
AND the document together. Look for words like:
  "and the document", "and the report", "and the pdf",
  "data and document", "document and data",
  "both", "combine", "together", "also the document",
  "tell about", "tell me about both",
  "summarise the data and", "summarise document and data"
Examples:
  "summarise the data and the document"
  "tell about the data and document too"
  "what does the data show and what does the report say?"
  "combine insights from both sources"
  "summarise document and data"
  "give me insights from data and report"

"general" — greeting, capability question, or unrelated.
Examples: "hi", "what can you do?", "help"

IMPORTANT:
- If the question mentions document/report/pdf AND data/numbers
  together → ALWAYS classify as "both"
- If unsure between analytics and both, and a PDF is uploaded
  → classify as "both"

Reply with ONLY ONE WORD: analytics, rag, both, or general"""


ANALYTICS_NODE_PROMPT = """You are a business analyst. Based on this data analysis result, 
answer the user's question directly and specifically.

Data analysis result:
{analytics_result}

User question: {question}

Rules:
- Use specific numbers from the analysis
- Be direct and actionable
- If you see a negative trend, say so and suggest why it might be happening
- Keep response under 200 words
- Do not say "based on the analysis" — just state findings"""


RAG_NODE_PROMPT = """You are a business analyst reading company documents.
Answer the user's question using ONLY the document excerpts below.
Always cite which document/page you used like [Page 3] or [Source: quarterly_report.pdf].
If the answer isn't in the documents, say "The uploaded documents don't cover this."

Document excerpts:
{rag_context}

User question: {question}"""


SYNTHESISER_PROMPT = """You are a senior business analyst
giving a briefing to a retail business manager.

You have access to: {context_description}

{analytics_section}

{rag_section}

User question: "{question}"

Recent conversation:
{chat_history}

---

STRICT RULES:
1. Answer ONLY the question asked: "{question}"
2. If you have BOTH data analysis AND document content,
   you MUST use both — structure your answer as:
   📊 From the data: [specific numbers and findings]
   📄 From the document: [what the document adds or confirms]
   💡 Combined insight: [your integrated recommendation]
3. If you have only data → give specific numbers and one recommendation
4. If you have only document → summarise key points with citations
5. NEVER say "there is no context" if analytics_section or
   rag_section has content above
6. Use specific numbers from the data
7. Cite document sources like [Page 3] or [Source: report.pdf]
8. Maximum 200 words
9. End with one concrete, actionable recommendation

EXAMPLE of a good combined answer:
Q: Summarise the data and document

📊 From the data: Sales total $2.3M across 9,994 orders
(Jan 2018 – Dec 2021). Standard Class dominates shipping
at $1.36M. Technology leads categories at $836K.

📄 From the document: The demand forecasting report
identifies Q4 as the peak demand period and recommends
increasing Technology inventory by 15% pre-October.

💡 Combined insight: Standard Class shipping aligns well
with the high-volume Technology orders the report flags
for Q4. Prioritise restocking Technology via Standard Class
before October to capture peak demand.

Now answer: "{question}" """


COLUMN_DETECTIVE_PROMPT = """You are a data analyst helper. You need to map a user's question to the correct columns of a pandas DataFrame.

The DataFrame has these columns grouped by type:
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Date/Temporal columns: {date_cols}

User's question: "{question}"

Your job is to identify:
1. The most relevant numeric column for the question.
2. The most relevant categorical column (to group by or analyze).
3. The most relevant date column (if trend or temporal analysis is needed).

Rules:
- Select only from the columns listed above.
- If a column of a certain type is not relevant to the question, return null or an empty string for that field.
- Return a JSON object with keys: "numeric_col", "categorical_col", "date_col".
- Do not include any other text, markdown formatting, or explanation. Return ONLY the JSON object.

Example JSON output:
{{"numeric_col": "sales_amount", "categorical_col": "product_name", "date_col": "date"}}
"""

