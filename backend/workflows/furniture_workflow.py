"""
LangGraph Furniture Analysis Workflow
Orchestrates AI agents for complete furniture listing automation
"""
import asyncio
import uuid
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import redis
import json
import logging
from datetime import datetime

# Import agents
from agents.vision_agent import VisionAnalysisAgent
from agents.brand_agent import BrandRecognitionAgent
from agents.market_agent import MarketResearchAgent
from agents.pricing_agent import PricingIntelligenceAgent
from agents.listing_agent import ListingGenerationAgent
from agents.qa_agent import QualityAssuranceAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FurnitureAnalysisState(TypedDict):
    """State shared between all agents"""
    # Input
    workflow_id: str
    images: List[str]  # Image file paths
    user_preferences: Optional[Dict[str, Any]]
    
    # Agent Outputs
    vision_analysis: Optional[Dict[str, Any]]
    brand_info: Optional[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]]
    pricing_analysis: Optional[Dict[str, Any]]
    generated_listing: Optional[Dict[str, Any]]
    qa_results: Optional[Dict[str, Any]]
    
    # Metadata
    confidence_scores: Dict[str, float]
    processing_time: Dict[str, float]
    errors: List[str]
    warnings: List[str]
    current_step: str
    completed_steps: List[str]
    
    # Final Output
    final_listing: Optional[Dict[str, Any]]
    success: bool

class FurnitureWorkflowEngine:
    """Main workflow engine using LangGraph"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_saver = MemorySaver()
        self.workflow = self._create_workflow()
        
        # Initialize agents
        self.agents = {
            'vision': VisionAnalysisAgent(),
            'brand': BrandRecognitionAgent(),
            'market': MarketResearchAgent(),
            'pricing': PricingIntelligenceAgent(),
            'listing': ListingGenerationAgent(),
            'qa': QualityAssuranceAgent()
        }
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(FurnitureAnalysisState)
        
        # Add agent nodes
        workflow.add_node("vision_analysis", self._vision_node)
        workflow.add_node("brand_recognition", self._brand_node)
        workflow.add_node("market_research", self._market_node)
        workflow.add_node("pricing_intelligence", self._pricing_node)
        workflow.add_node("listing_generation", self._listing_node)
        workflow.add_node("quality_assurance", self._qa_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define workflow edges
        workflow.add_edge(START, "vision_analysis")
        workflow.add_edge("vision_analysis", "brand_recognition")
        workflow.add_edge("brand_recognition", "market_research")
        workflow.add_edge("market_research", "pricing_intelligence")
        workflow.add_edge("pricing_intelligence", "listing_generation")
        workflow.add_edge("listing_generation", "quality_assurance")
        workflow.add_edge("quality_assurance", "finalize")
        workflow.add_edge("finalize", END)
        
        # Set entry point
        workflow.set_entry_point("vision_analysis")
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    async def _vision_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Vision analysis agent node"""
        logger.info(f"Starting vision analysis for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'vision_analysis'
            await self._cache_state(state)
            
            # Run vision analysis
            vision_result = await self.agents['vision'].analyze_images(state['images'])
            
            state['vision_analysis'] = vision_result
            state['confidence_scores']['vision'] = vision_result.get('confidence', 0.0)
            state['completed_steps'].append('vision_analysis')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['vision'] = processing_time
            
            logger.info(f"Vision analysis completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Vision analysis failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _brand_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Brand recognition agent node"""
        logger.info(f"Starting brand recognition for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'brand_recognition'
            await self._cache_state(state)
            
            # Run brand recognition using vision analysis
            vision_data = state.get('vision_analysis', {})
            brand_result = await self.agents['brand'].identify_brand(
                images=state['images'],
                vision_context=vision_data
            )
            
            state['brand_info'] = brand_result
            state['confidence_scores']['brand'] = brand_result.get('confidence', 0.0)
            state['completed_steps'].append('brand_recognition')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['brand'] = processing_time
            
            logger.info(f"Brand recognition completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Brand recognition failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _market_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Market research agent node"""
        logger.info(f"Starting market research for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'market_research'
            await self._cache_state(state)
            
            # Combine vision and brand data for market research
            search_context = {
                'vision': state.get('vision_analysis', {}),
                'brand': state.get('brand_info', {})
            }
            
            market_result = await self.agents['market'].research_market_prices(
                context=search_context
            )
            
            state['market_data'] = market_result
            state['confidence_scores']['market'] = market_result.get('confidence', 0.0)
            state['completed_steps'].append('market_research')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['market'] = processing_time
            
            logger.info(f"Market research completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Market research failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _pricing_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Pricing intelligence agent node"""
        logger.info(f"Starting pricing analysis for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'pricing_intelligence'
            await self._cache_state(state)
            
            # Combine all data for intelligent pricing
            pricing_context = {
                'vision': state.get('vision_analysis', {}),
                'brand': state.get('brand_info', {}),
                'market': state.get('market_data', {})
            }
            
            pricing_result = await self.agents['pricing'].calculate_optimal_pricing(
                context=pricing_context
            )
            
            state['pricing_analysis'] = pricing_result
            state['confidence_scores']['pricing'] = pricing_result.get('confidence', 0.0)
            state['completed_steps'].append('pricing_intelligence')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['pricing'] = processing_time
            
            logger.info(f"Pricing analysis completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Pricing analysis failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _listing_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Listing generation agent node"""
        logger.info(f"Starting listing generation for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'listing_generation'
            await self._cache_state(state)
            
            # Combine all analysis for listing generation
            listing_context = {
                'vision': state.get('vision_analysis', {}),
                'brand': state.get('brand_info', {}),
                'market': state.get('market_data', {}),
                'pricing': state.get('pricing_analysis', {}),
                'images': state['images']
            }
            
            listing_result = await self.agents['listing'].generate_listing(
                context=listing_context
            )
            
            state['generated_listing'] = listing_result
            state['confidence_scores']['listing'] = listing_result.get('confidence', 0.0)
            state['completed_steps'].append('listing_generation')
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['listing'] = processing_time
            
            logger.info(f"Listing generation completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Listing generation failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _qa_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Quality assurance agent node"""
        logger.info(f"Starting quality assurance for workflow {state['workflow_id']}")
        start_time = datetime.now()
        
        try:
            state['current_step'] = 'quality_assurance'
            await self._cache_state(state)
            
            # Quality check the generated listing
            qa_context = {
                'listing': state.get('generated_listing', {}),
                'confidence_scores': state.get('confidence_scores', {}),
                'all_data': {
                    'vision': state.get('vision_analysis', {}),
                    'brand': state.get('brand_info', {}),
                    'market': state.get('market_data', {}),
                    'pricing': state.get('pricing_analysis', {})
                }
            }
            
            qa_result = await self.agents['qa'].validate_listing(
                context=qa_context
            )
            
            state['qa_results'] = qa_result
            state['confidence_scores']['qa'] = qa_result.get('confidence', 0.0)
            state['completed_steps'].append('quality_assurance')
            
            # Add any QA warnings
            if qa_result.get('warnings'):
                state['warnings'].extend(qa_result['warnings'])
            
            processing_time = (datetime.now() - start_time).total_seconds()
            state['processing_time']['qa'] = processing_time
            
            logger.info(f"Quality assurance completed in {processing_time:.2f}s")
            
        except Exception as e:
            error_msg = f"Quality assurance failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        await self._cache_state(state)
        return state
    
    async def _finalize_node(self, state: FurnitureAnalysisState) -> FurnitureAnalysisState:
        """Finalize the workflow and prepare final output"""
        logger.info(f"Finalizing workflow {state['workflow_id']}")
        
        try:
            state['current_step'] = 'finalization'
            
            # Create final listing with all enhancements
            final_listing = state.get('generated_listing', {})
            qa_results = state.get('qa_results', {})
            
            # Apply QA improvements if any
            if qa_results.get('improvements'):
                final_listing.update(qa_results['improvements'])
            
            # Add metadata
            final_listing['workflow_metadata'] = {
                'workflow_id': state['workflow_id'],
                'confidence_scores': state['confidence_scores'],
                'processing_time': state['processing_time'],
                'total_time': sum(state['processing_time'].values()),
                'completed_steps': state['completed_steps'],
                'warnings': state['warnings'],
                'agent_method': 'LANGGRAPH_AI_AGENTS'
            }
            
            state['final_listing'] = final_listing
            state['success'] = len(state['errors']) == 0
            state['completed_steps'].append('finalization')
            
            logger.info(f"Workflow {state['workflow_id']} completed successfully")
            
        except Exception as e:
            error_msg = f"Finalization failed: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['success'] = False
        
        await self._cache_state(state)
        return state
    
    async def _cache_state(self, state: FurnitureAnalysisState):
        """Cache workflow state in Redis"""
        if self.redis_client:
            try:
                cache_key = f"workflow:{state['workflow_id']}"
                # Convert state to JSON-serializable format
                cache_data = {
                    'workflow_id': state['workflow_id'],
                    'current_step': state.get('current_step'),
                    'completed_steps': state.get('completed_steps', []),
                    'confidence_scores': state.get('confidence_scores', {}),
                    'processing_time': state.get('processing_time', {}),
                    'errors': state.get('errors', []),
                    'warnings': state.get('warnings', []),
                    'success': state.get('success', False)
                }
                
                await self.redis_client.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Failed to cache state: {e}")
    
    async def run_workflow(self, images: List[str], user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the complete furniture analysis workflow"""
        workflow_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state: FurnitureAnalysisState = {
            'workflow_id': workflow_id,
            'images': images,
            'user_preferences': user_preferences or {},
            'vision_analysis': None,
            'brand_info': None,
            'market_data': None,
            'pricing_analysis': None,
            'generated_listing': None,
            'qa_results': None,
            'confidence_scores': {},
            'processing_time': {},
            'errors': [],
            'warnings': [],
            'current_step': 'initializing',
            'completed_steps': [],
            'final_listing': None,
            'success': False
        }
        
        logger.info(f"Starting workflow {workflow_id} with {len(images)} images")
        
        try:
            # Run the workflow
            config = {"configurable": {"thread_id": workflow_id}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            return {
                "success": final_state.get('success', False),
                "workflow_id": workflow_id,
                "listing": final_state.get('final_listing'),
                "metadata": {
                    "confidence_scores": final_state.get('confidence_scores', {}),
                    "processing_time": final_state.get('processing_time', {}),
                    "total_time": sum(final_state.get('processing_time', {}).values()),
                    "completed_steps": final_state.get('completed_steps', []),
                    "warnings": final_state.get('warnings', []),
                    "errors": final_state.get('errors', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "metadata": {
                    "completed_steps": [],
                    "errors": [str(e)]
                }
            }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status from cache"""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        try:
            cache_key = f"workflow:{workflow_id}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            else:
                return {"error": "Workflow not found"}
                
        except Exception as e:
            return {"error": f"Failed to get status: {str(e)}"}

# Create global workflow engine instance
workflow_engine = None

def get_workflow_engine(redis_client=None) -> FurnitureWorkflowEngine:
    """Get or create workflow engine instance"""
    global workflow_engine
    if workflow_engine is None:
        workflow_engine = FurnitureWorkflowEngine(redis_client)
    return workflow_engine
