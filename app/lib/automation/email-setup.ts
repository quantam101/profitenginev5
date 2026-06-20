/**
 * EMAIL AUTOMATION
 *
 * Automatically setup and manage email sequences:
 * - Read premium onboarding sequences from PREMIUM_ONBOARDING_SEQUENCE.md
 * - Setup automation in Klaviyo/Substack/ConvertKit via API
 * - Auto-trigger sequences on free trial signup
 * - Track engagement and conversions
 *
 * Environment Requirements:
 * - EMAIL_SERVICE: 'klaviyo' | 'convertkit' | 'substack' | 'beehiiv'
 * - KLAVIYO_API_KEY (if using Klaviyo)
 * - CONVERTKIT_API_KEY (if using ConvertKit)
 * - SUBSTACK_API_TOKEN (if using Substack)
 * - BEEHIIV_API_KEY (if using Beehiiv)
 */

import { readFile } from 'fs/promises';

interface EmailSequenceStep {
  order: number;
  delayHours: number;
  subject: string;
  content: string;
  ctaText?: string;
  ctaLink?: string;
  tags?: string[];
  conditional?: {
    field: string;
    operator: 'equals' | 'contains' | 'greater_than';
    value: string;
  };
}

interface EmailSequence {
  name: string;
  description: string;
  trigger: 'signup' | 'trial_start' | 'cart_abandoned' | 'purchase';
  steps: EmailSequenceStep[];
  successMetrics?: {
    openRate?: number;
    clickRate?: number;
    conversionRate?: number;
  };
}

interface EmailAutomationSetup {
  sequenceId: string;
  sequenceName: string;
  stepCount: number;
  triggerType: string;
  createdAt: string;
}

interface EmailAutomationResult {
  success: boolean;
  setupSequences?: EmailAutomationSetup[];
  totalSequences?: number;
  error?: string;
  configuration?: Record<string, string>;
}

/**
 * Parse email sequences from PREMIUM_ONBOARDING_SEQUENCE.md
 */
async function parseEmailSequences(
  filePath: string = 'PREMIUM_ONBOARDING_SEQUENCE.md'
): Promise<EmailSequence[]> {
  try {
    const content = await readFile(filePath, 'utf-8');
    const sequences: EmailSequence[] = [];

    // Split by top-level sequence headers
    const sequenceMatches = content.matchAll(/## Sequence: (.+?)\n\n(.+?)(?=## Sequence:|$)/gs);

    for (const match of sequenceMatches) {
      const sequenceName = match[1];
      const sequenceContent = match[2];

      // Extract description
      const descMatch = sequenceContent.match(/\*\*Description\*\*[:\n]+(.+?)(?=\n\n|###)/is);

      // Extract trigger
      const triggerMatch = sequenceContent.match(/\*\*Trigger\*\*[:\n]+(.+?)(?=\n\n|###)/i);

      // Extract emails
      const emailMatches = sequenceContent.matchAll(
        /### Email (\d+): (.+?)\n\n(.+?)(?=### Email |\n\n##|$)/gs
      );

      const steps: EmailSequenceStep[] = [];

      for (const emailMatch of emailMatches) {
        const emailNumber = parseInt(emailMatch[1], 10);
        const emailTitle = emailMatch[2];
        const emailContent = emailMatch[3];

        // Parse email details
        const delayMatch = emailContent.match(/\*\*Send After\*\*[:\n]+(\d+)\s*(?:hour|hr)/i);
        const subjectMatch = emailContent.match(/\*\*Subject\*\*[:\n]+(.+?)(?=\n|###)/i);
        const ctaMatch = emailContent.match(/\*\*CTA\*\*[:\n]+(.+?)(?=\n|###)/i);
        const linkMatch = emailContent.match(/\*\*CTA Link\*\*[:\n]+(\S+)/i);

        steps.push({
          order: emailNumber,
          delayHours: delayMatch ? parseInt(delayMatch[1], 10) : emailNumber * 24,
          subject: subjectMatch ? subjectMatch[1].trim() : emailTitle,
          content: emailContent,
          ctaText: ctaMatch ? ctaMatch[1].trim() : 'Learn More',
          ctaLink: linkMatch ? linkMatch[1].trim() : undefined,
          tags: ['premium-onboarding', `email-${emailNumber}`],
        });
      }

      sequences.push({
        name: sequenceName,
        description: descMatch ? descMatch[1].trim() : sequenceName,
        trigger: (triggerMatch ? triggerMatch[1].toLowerCase().includes('trial') ? 'trial_start' : 'signup' : 'signup') as
          | 'signup'
          | 'trial_start'
          | 'cart_abandoned'
          | 'purchase',
        steps,
      });
    }

    return sequences;
  } catch (error) {
    console.error(`Failed to parse email sequences: ${error}`);
    return [];
  }
}

/**
 * Setup sequences in Klaviyo
 */
async function setupKlaviyoSequences(sequences: EmailSequence[]): Promise<EmailAutomationSetup[]> {
  const klaviyoKey = process.env.KLAVIYO_API_KEY;

  if (!klaviyoKey) {
    throw new Error('KLAVIYO_API_KEY not configured');
  }

  const setupSequences: EmailAutomationSetup[] = [];

  for (const sequence of sequences) {
    try {
      // Create flow (sequence) in Klaviyo
      const flowResponse = await fetch('https://a.klaviyo.com/api/flows/', {
        method: 'POST',
        headers: {
          Authorization: `Klaviyo-API-Key ${klaviyoKey}`,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          data: {
            type: 'flow',
            attributes: {
              name: sequence.name,
              status: 'draft',
              trigger: {
                type: sequence.trigger,
              },
            },
          },
        }),
      });

      if (!flowResponse.ok) {
        console.warn(
          `Klaviyo flow creation failed: ${sequence.name} - ${await flowResponse.text()}`
        );
        continue;
      }

      const flowData = (await flowResponse.json()) as { data: { id: string } };
      const flowId = flowData.data.id;

      // Add emails to flow
      for (const step of sequence.steps) {
        const emailResponse = await fetch('https://a.klaviyo.com/api/emails/', {
          method: 'POST',
          headers: {
            Authorization: `Klaviyo-API-Key ${klaviyoKey}`,
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({
            data: {
              type: 'email',
              attributes: {
                subject: step.subject,
                from_email: 'trading@alreadyherellc.com',
                from_label: 'ProfitEngine',
                reply_to_email: 'support@alreadyherellc.com',
                html: generateEmailHTML(step),
              },
              relationships: {
                flow: {
                  data: {
                    type: 'flow',
                    id: flowId,
                  },
                },
              },
            },
          }),
        });

        if (!emailResponse.ok) {
          console.warn(`Klaviyo email creation failed: ${step.subject}`);
        }
      }

      setupSequences.push({
        sequenceId: flowId,
        sequenceName: sequence.name,
        stepCount: sequence.steps.length,
        triggerType: sequence.trigger,
        createdAt: new Date().toISOString(),
      });

      console.log(`✓ Created Klaviyo flow: ${sequence.name} (${sequence.steps.length} emails)`);
    } catch (error) {
      console.error(`Failed to setup Klaviyo sequence: ${sequence.name} - ${error}`);
    }
  }

  return setupSequences;
}

/**
 * Setup sequences in ConvertKit
 */
async function setupConvertKitSequences(sequences: EmailSequence[]): Promise<EmailAutomationSetup[]> {
  const convertKitKey = process.env.CONVERTKIT_API_KEY;

  if (!convertKitKey) {
    throw new Error('CONVERTKIT_API_KEY not configured');
  }

  const setupSequences: EmailAutomationSetup[] = [];

  for (const sequence of sequences) {
    try {
      // Create sequence (called "automation" in ConvertKit)
      const automationResponse = await fetch(
        `https://api.convertkit.com/v3/automations?api_key=${convertKitKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            automation: {
              name: sequence.name,
              description: sequence.description,
              trigger_type: sequence.trigger,
              emails: sequence.steps.map((step) => ({
                subject: step.subject,
                delay_seconds: step.delayHours * 3600,
                body: step.content,
                cta_text: step.ctaText,
                cta_link: step.ctaLink,
              })),
            },
          }),
        }
      );

      if (!automationResponse.ok) {
        console.warn(
          `ConvertKit automation creation failed: ${sequence.name} - ${await automationResponse.text()}`
        );
        continue;
      }

      const automationData = (await automationResponse.json()) as {
        automation: { id: number };
      };

      setupSequences.push({
        sequenceId: automationData.automation.id.toString(),
        sequenceName: sequence.name,
        stepCount: sequence.steps.length,
        triggerType: sequence.trigger,
        createdAt: new Date().toISOString(),
      });

      console.log(
        `✓ Created ConvertKit automation: ${sequence.name} (${sequence.steps.length} emails)`
      );
    } catch (error) {
      console.error(`Failed to setup ConvertKit sequence: ${sequence.name} - ${error}`);
    }
  }

  return setupSequences;
}

/**
 * Setup sequences in Substack
 */
async function setupSubstackSequences(sequences: EmailSequence[]): Promise<EmailAutomationSetup[]> {
  const substackToken = process.env.SUBSTACK_API_TOKEN;

  if (!substackToken) {
    throw new Error('SUBSTACK_API_TOKEN not configured');
  }

  const setupSequences: EmailAutomationSetup[] = [];

  for (const sequence of sequences) {
    try {
      // Create publication sequence in Substack
      const sequenceResponse = await fetch(
        'https://substack.com/api/v1/sequences',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${substackToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: sequence.name,
            description: sequence.description,
            emails: sequence.steps.map((step) => ({
              subject: step.subject,
              body: step.content,
              delay_hours: step.delayHours,
              cta_link: step.ctaLink,
            })),
          }),
        }
      );

      if (!sequenceResponse.ok) {
        console.warn(
          `Substack sequence creation failed: ${sequence.name} - ${await sequenceResponse.text()}`
        );
        continue;
      }

      const sequenceData = (await sequenceResponse.json()) as { id: string };

      setupSequences.push({
        sequenceId: sequenceData.id,
        sequenceName: sequence.name,
        stepCount: sequence.steps.length,
        triggerType: sequence.trigger,
        createdAt: new Date().toISOString(),
      });

      console.log(`✓ Created Substack sequence: ${sequence.name} (${sequence.steps.length} emails)`);
    } catch (error) {
      console.error(`Failed to setup Substack sequence: ${sequence.name} - ${error}`);
    }
  }

  return setupSequences;
}

/**
 * Setup sequences in Beehiiv
 */
async function setupBeehiivSequences(sequences: EmailSequence[]): Promise<EmailAutomationSetup[]> {
  const beehiivKey = process.env.BEEHIIV_API_KEY;

  if (!beehiivKey) {
    throw new Error('BEEHIIV_API_KEY not configured');
  }

  const setupSequences: EmailAutomationSetup[] = [];

  for (const sequence of sequences) {
    try {
      // Create automation workflow in Beehiiv
      const workflowResponse = await fetch(
        'https://api.beehiiv.com/v1/workflows',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${beehiivKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: sequence.name,
            description: sequence.description,
            trigger: sequence.trigger,
            actions: sequence.steps.map((step) => ({
              type: 'send_email',
              delay: step.delayHours,
              email: {
                subject: step.subject,
                body: step.content,
                cta_link: step.ctaLink,
              },
            })),
          }),
        }
      );

      if (!workflowResponse.ok) {
        console.warn(
          `Beehiiv workflow creation failed: ${sequence.name} - ${await workflowResponse.text()}`
        );
        continue;
      }

      const workflowData = (await workflowResponse.json()) as { id: string };

      setupSequences.push({
        sequenceId: workflowData.id,
        sequenceName: sequence.name,
        stepCount: sequence.steps.length,
        triggerType: sequence.trigger,
        createdAt: new Date().toISOString(),
      });

      console.log(`✓ Created Beehiiv workflow: ${sequence.name} (${sequence.steps.length} emails)`);
    } catch (error) {
      console.error(`Failed to setup Beehiiv sequence: ${sequence.name} - ${error}`);
    }
  }

  return setupSequences;
}

/**
 * Generate HTML email from content
 */
function generateEmailHTML(step: EmailSequenceStep): string {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #1a1a1a; color: #fff; padding: 20px; border-radius: 4px; margin-bottom: 20px; }
    .content { margin: 20px 0; }
    .cta { display: inline-block; background: #007bff; color: #fff; padding: 10px 20px; border-radius: 4px; text-decoration: none; }
    .footer { font-size: 12px; color: #666; margin-top: 40px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ProfitEngine</h1>
      <p>${step.subject}</p>
    </div>
    <div class="content">
      ${step.content.replace(/\n/g, '<br/>')}
    </div>
    ${step.ctaLink ? `
    <div style="text-align: center; margin: 30px 0;">
      <a href="${step.ctaLink}" class="cta">${step.ctaText || 'Learn More'}</a>
    </div>
    ` : ''}
    <div class="footer">
      <p>Already Here LLC | Trading & Market Analysis</p>
      <p>
        <a href="https://profitengine.alreadyherellc.com/unsubscribe">Unsubscribe</a>
      </p>
    </div>
  </div>
</body>
</html>
  `;
}

/**
 * Main orchestration function: Setup all email sequences
 */
export async function setupEmailSequences(): Promise<EmailAutomationResult> {
  try {
    const emailService = process.env.EMAIL_SERVICE || 'beehiiv';

    console.log(`Setting up email automation via ${emailService}...`);

    // Parse email sequences
    const sequences = await parseEmailSequences('PREMIUM_ONBOARDING_SEQUENCE.md');

    if (sequences.length === 0) {
      return {
        success: false,
        error: 'No email sequences found',
      };
    }

    console.log(`Parsed ${sequences.length} sequences`);

    // Setup sequences based on email service
    let setupSequences: EmailAutomationSetup[] = [];

    if (emailService === 'klaviyo') {
      setupSequences = await setupKlaviyoSequences(sequences);
    } else if (emailService === 'convertkit') {
      setupSequences = await setupConvertKitSequences(sequences);
    } else if (emailService === 'substack') {
      setupSequences = await setupSubstackSequences(sequences);
    } else if (emailService === 'beehiiv') {
      setupSequences = await setupBeehiivSequences(sequences);
    }

    const configuration: Record<string, string> = {
      EMAIL_SERVICE: emailService,
      SEQUENCES_CREATED: setupSequences.length.toString(),
      TOTAL_EMAILS: setupSequences.reduce((acc, seq) => acc + seq.stepCount, 0).toString(),
      SETUP_TIME: new Date().toISOString(),
    };

    return {
      success: setupSequences.length > 0,
      setupSequences,
      totalSequences: sequences.length,
      configuration,
    };
  } catch (error) {
    return {
      success: false,
      error: `Email automation setup failed: ${error}`,
    };
  }
}

export { EmailSequence, EmailSequenceStep, EmailAutomationSetup, EmailAutomationResult };
