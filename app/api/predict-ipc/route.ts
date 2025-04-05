import { NextResponse } from "next/server"

// Mock IPC sections data for prediction
const ipcSections = [
  {
    section: "IPC 420",
    description: "Cheating and dishonestly inducing delivery of property",
    confidence: 98,
    punishment:
      "Imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.",
    relevance: "The case involves deception to obtain property, which is a key element of IPC 420.",
  },
  {
    section: "IPC 406",
    description: "Punishment for criminal breach of trust",
    confidence: 85,
    punishment:
      "Imprisonment of either description for a term which may extend to three years, or with fine, or with both.",
    relevance: "The property was entrusted to the accused who then misappropriated it, constituting a breach of trust.",
  },
  {
    section: "IPC 34",
    description: "Acts done by several persons in furtherance of common intention",
    confidence: 72,
    punishment: "Each person is liable for the act in the same manner as if it were done by him alone.",
    relevance: "Multiple individuals were involved in the execution of the offense with a shared intention.",
  },
  {
    section: "IPC 120B",
    description: "Punishment of criminal conspiracy",
    confidence: 65,
    punishment: "Same as that provided for the abetment of the offence which is the object of the conspiracy.",
    relevance: "There was a planned agreement between multiple parties to commit the offense.",
  },
  {
    section: "IPC 415",
    description: "Cheating",
    confidence: 60,
    punishment: "Varies based on the specific circumstances of the cheating.",
    relevance: "The accused deceived the victim by fraudulent or dishonest means.",
  },
]

// Simple keyword-based prediction function
function predictIPCSections(description: string) {
  const keywords = {
    theft: ["IPC 378", "IPC 379", "IPC 380"],
    robbery: ["IPC 390", "IPC 392", "IPC 394"],
    murder: ["IPC 302", "IPC 304", "IPC 300"],
    assault: ["IPC 351", "IPC 352", "IPC 354"],
    fraud: ["IPC 420", "IPC 415", "IPC 406"],
    cheating: ["IPC 420", "IPC 415", "IPC 417"],
    property: ["IPC 425", "IPC 426", "IPC 427"],
    criminal: ["IPC 120B", "IPC 34", "IPC 149"],
    conspiracy: ["IPC 120A", "IPC 120B", "IPC 107"],
    breach: ["IPC 405", "IPC 406", "IPC 409"],
    trust: ["IPC 405", "IPC 406", "IPC 409"],
    forgery: ["IPC 463", "IPC 464", "IPC 465"],
    document: ["IPC 463", "IPC 464", "IPC 466"],
    trespass: ["IPC 441", "IPC 447", "IPC 448"],
    hurt: ["IPC 319", "IPC 323", "IPC 324"],
    kidnapping: ["IPC 359", "IPC 360", "IPC 363"],
    abduction: ["IPC 362", "IPC 363", "IPC 366"],
    rape: ["IPC 375", "IPC 376", "IPC 376A"],
    defamation: ["IPC 499", "IPC 500", "IPC 501"],
    extortion: ["IPC 383", "IPC 384", "IPC 385"],
    bribery: ["IPC 171B", "IPC 171C", "IPC 171E"],
    corruption: ["IPC 171B", "IPC 171C", "IPC 171E"],
    riot: ["IPC 146", "IPC 147", "IPC 148"],
    unlawful: ["IPC 141", "IPC 142", "IPC 143"],
    assembly: ["IPC 141", "IPC 142", "IPC 143"],
    sedition: ["IPC 124A", "IPC 153A", "IPC 153B"],
    counterfeit: ["IPC 489A", "IPC 489B", "IPC 489C"],
    currency: ["IPC 489A", "IPC 489B", "IPC 489C"],
    suicide: ["IPC 305", "IPC 306", "IPC 309"],
    dowry: ["IPC 304B", "IPC 498A"],
    cruelty: ["IPC 498A", "IPC 323", "IPC 324"],
    negligence: ["IPC 304A", "IPC 279", "IPC 337"],
    accident: ["IPC 304A", "IPC 279", "IPC 337"],
    mischief: ["IPC 425", "IPC 426", "IPC 427"],
    damage: ["IPC 425", "IPC 426", "IPC 427"],
    obscene: ["IPC 292", "IPC 293", "IPC 294"],
    insult: ["IPC 504", "IPC 509"],
    modesty: ["IPC 354", "IPC 509"],
    woman: ["IPC 354", "IPC 509", "IPC 376"],
    false: ["IPC 191", "IPC 192", "IPC 193"],
    evidence: ["IPC 191", "IPC 192", "IPC 193"],
    perjury: ["IPC 191", "IPC 192", "IPC 193"],
    intimidation: ["IPC 503", "IPC 506", "IPC 507"],
    threat: ["IPC 503", "IPC 506", "IPC 507"],
    impersonation: ["IPC 416", "IPC 419"],
    identity: ["IPC 416", "IPC 419"],
    gambling: ["IPC 294A"],
    lottery: ["IPC 294A"],
    public: ["IPC 268", "IPC 269", "IPC 270"],
    nuisance: ["IPC 268", "IPC 290", "IPC 291"],
    obstruction: ["IPC 283", "IPC 341", "IPC 283"],
    escape: ["IPC 224", "IPC 225", "IPC 225B"],
    custody: ["IPC 224", "IPC 225", "IPC 225B"],
    abetment: ["IPC 107", "IPC 108", "IPC 109"],
    attempt: ["IPC 511", "IPC 307", "IPC 308"],
    criminal: ["IPC 120B", "IPC 34", "IPC 149"],
    intention: ["IPC 34", "IPC 149", "IPC 120A"],
    common: ["IPC 34", "IPC 149", "IPC 120A"],
  }

  // Convert description to lowercase for case-insensitive matching
  const lowerDescription = description.toLowerCase()

  // Count occurrences of keywords in the description
  const sectionCounts = {}

  // Check for each keyword in the description
  Object.entries(keywords).forEach(([keyword, sections]) => {
    if (lowerDescription.includes(keyword)) {
      sections.forEach((section) => {
        sectionCounts[section] = (sectionCounts[section] || 0) + 1
      })
    }
  })

  // Sort sections by count (most relevant first)
  const sortedSections = Object.entries(sectionCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([section]) => section)

  // Get the top 3 most relevant sections
  const topSections = sortedSections.slice(0, 3)

  // If no keywords matched, return default sections
  if (topSections.length === 0) {
    return ipcSections
  }

  // Map the top sections to our predefined data or create new entries
  const results = topSections.map((section, index) => {
    // Try to find the section in our predefined data
    const predefinedSection = ipcSections.find((s) => s.section === section)

    if (predefinedSection) {
      // Adjust confidence based on position
      return {
        ...predefinedSection,
        confidence: Math.max(60, 98 - index * 15), // 98%, 83%, 68% for top 3
      }
    } else {
      // Create a new entry for sections not in our predefined data
      return {
        section: section,
        description: `${section} of the Indian Penal Code`,
        confidence: Math.max(60, 98 - index * 15),
        punishment: "Punishment as prescribed by law for this offense.",
        relevance: "This section appears relevant based on the description provided.",
      }
    }
  })

  return results
}

export async function POST(request: Request) {
  try {
    const { description } = await request.json()

    if (!description) {
      return NextResponse.json({ error: "Description is required" }, { status: 400 })
    }

    // Simulate processing time
    await new Promise((resolve) => setTimeout(resolve, 1500))

    // Get predictions based on the description
    const predictions = predictIPCSections(description)

    return NextResponse.json({ predictions })
  } catch (error) {
    console.error("Prediction error:", error)
    return NextResponse.json({ error: "Failed to process prediction" }, { status: 500 })
  }
}

