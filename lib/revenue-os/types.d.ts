import type { ObjectId } from 'mongodb';

export type RevenuePlayStatus =
  | 'SEED_READY'
  | 'RESEARCH'
  | 'ACTIVE'
  | 'PAUSED'
  | 'ARCHIVED';

export type TicketUnit = 'dispatch' | 'project' | 'month' | 'route' | 'location';

export interface EstimatedTicketValue {
  minimum: number;
  maximum: number;
  unit: TicketUnit;
}

export interface ScoreInputs {
  dailyRevenuePotential: number;
  speedToFirstCash: number;
  repeatability: number;
  routeStacking: number;
  lowStartupCost: number;
  lowLiability: number;
  recurringRetainer: number;
  databaseAiValue: number;
}

export interface RevenuePlay {
  _id?: ObjectId | string;
  recordId: string;
  source: string;
  lane: string;
  revenuePlayName: string;
  buyerType: string;
  exampleTargetCompanyOrMarket: string;
  contactPath: string;
  location: string;
  painSolved: string;
  estimatedTicketValue: EstimatedTicketValue;
  costRequired: number;
  profitPotential: number;
  timeToRevenueDays: number;
  recurringPotential: number;
  stackingFit: number;
  liabilityScore: number;
  databaseValueScore: number;
  startupRequirements: string[];
  first10TargetStrategy: string;
  riskFlags: string[];
  recommendedAction: string;
  status: RevenuePlayStatus;
  nextFollowUpDate?: Date | string;
  notes: string;
  scoreInputs?: ScoreInputs;
  opportunityScore?: number;
  overallScore: number;
  createdAt: Date | string;
  updatedAt: Date | string;
}

export interface Company {
  _id?: ObjectId | string;
  legalName: string;
  displayName: string;
  website?: string;
  domain?: string;
  industry: string;
  companyType: string;
  locations: CompanyLocation[];
  serviceLanes: string[];
  source: string;
  qualificationStatus: string;
  duplicateKey: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface CompanyLocation {
  street?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  coordinates?: GeoLocation;
}

export interface Contact {
  _id?: ObjectId | string;
  companyId: ObjectId | string;
  fullName?: string;
  title?: string;
  email?: string;
  phone?: string;
  preferredChannel?: string;
  contactStatus: string;
  consentStatus: string;
  source: string;
  lastVerifiedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface GeoLocation {
  type: 'Point';
  coordinates: [number, number];
}

export type OpportunityStage =
  | 'Research'
  | 'Qualified'
  | 'Approval Needed'
  | 'Outreach Approved'
  | 'Contacted'
  | 'Conversation'
  | 'Proposal'
  | 'Negotiation'
  | 'Won'
  | 'Lost'
  | 'On Hold';

export interface Opportunity {
  _id?: ObjectId | string;
  revenuePlayId: ObjectId | string;
  companyId: ObjectId | string;
  contactIds: (ObjectId | string)[];
  title: string;
  stage: OpportunityStage;
  estimatedValue: number;
  recurringMonthlyValue: number;
  probability: number;
  weightedValue: number;
  location?: GeoLocation;
  nextAction: string;
  nextFollowUpDate?: Date;
  assignedTo?: string;
  approvalStatus: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Activity {
  _id?: ObjectId | string;
  entityType: string;
  entityId: ObjectId | string;
  actionType: string;
  actor: string;
  summary: string;
  metadata: Record<string, unknown>;
  createdAt: Date;
}

export interface SeedImportSummary {
  total: number;
  inserted: number;
  updated: number;
  unchanged: number;
  errors: string[];
  dryRun: boolean;
}

export type FollowUpStatus = 'OPEN' | 'COMPLETED' | 'SNOOZED' | 'CANCELLED';

export interface FollowUpTask {
  _id?: ObjectId | string;
  entityType: 'opportunity' | 'company' | 'contact' | 'revenue_play';
  entityId: ObjectId | string;
  type: string;
  summary: string;
  dueDate: Date;
  status: FollowUpStatus;
  assignedTo?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  completedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface SavedView {
  _id?: ObjectId | string;
  name: string;
  entityType: string;
  filters: Record<string, unknown>;
  sortBy: string;
  order: 'asc' | 'desc';
  createdBy: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DashboardSummary {
  activeOpportunities: number;
  weightedPipelineValue: number;
  monthlyRecurringPotential: number;
  followUpsDueToday: number;
  fastCashOpportunities: number;
  averageOpportunityScore: number;
  revenueWonThisMonth: number;
  revenueTargetProgress: number;
  topRecommendedActions: RecommendedAction[];
  pipelineByStage: Record<string, { count: number; value: number }>;
  highestScoringRevenuePlays: RevenuePlaySummary[];
  followUpsDue: FollowUpTaskSummary[];
}

export interface RecommendedAction {
  title: string;
  entityType: 'opportunity' | 'company' | 'contact' | 'revenue_play';
  entityId?: string;
  reason: string;
  score?: number;
  estimatedValue?: number;
}

export interface RevenuePlaySummary {
  recordId: string;
  revenuePlayName: string;
  lane: string;
  overallScore: number;
  location: string;
}

export interface FollowUpTaskSummary {
  id: string;
  entityType: string;
  summary: string;
  dueDate: string;
  priority: string;
}
