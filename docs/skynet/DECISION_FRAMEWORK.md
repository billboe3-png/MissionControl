# DECISION FRAMEWORK

## Priority Hierarchy

Decisions in SKYNET and Mission Control are ranked in the following order.

1. **Correctness**
   - Correctness is non-negotiable
   - An incorrect decision that halts operation is preferable to an incorrect decision that continues operation
   - Partial correctness is not correctness

2. **Safety**
   - Safety overrides all other priorities except security when in direct conflict
   - Safety includes operator safety, system stability, and data integrity
   - Uncertainty in safety analysis resolves in favor of caution

3. **Security**
   - Security overrides convenience, speed, and feature richness
   - Security exceptions require documented approval and time expiration
   - Security failures are treated as incidents regardless of operational impact

4. **Reliability**
   - Predictable behavior is preferred over peak performance
   - Reliability includes graceful degradation
   - Reliability includes recoverability

5. **Maintainability**
   - Easy-to-change systems outperform optimized-but-fragile systems over time
   - Maintainability includes testability, observability, and documentation
   - Technical debt is measured and managed

6. **Performance**
   - Performance is valuable only when correctness, safety, security, and maintainability are satisfied
   - Optimize based on measurement
   - Optimize with clear success criteria

7. **Scalability**
   - Scale must preserve all higher-order priorities
   - Scale does not justify reduced security or safety
   - Scale decisions include operational cost and complexity

8. **Developer Experience**
   - Developer experience reduces defects and increases velocity
   - Developer convenience never overrides operator safety

9. **Operational Experience**
   - Operational simplicity is valued
   - Operator clarity is valued over automation cleverness
   - Under high-stress conditions, the simplest path is usually the correct path

## Trade-Off Analysis

Every trade-off must explicitly state:
- Option A
- Option B
- Higher-priority constraints satisfied by each
- Lower-priority constraint sacrificed by each
- Risk profile
- Reversibility
- Time horizon

Trade-offs are recorded in decision logs for future accountability.

## Risk Analysis

Risk is categorized by:
- Likelihood
- Impact
- Detectability
- Reversibility

Risk analysis requirements:
- all major decisions have explicit risk analysis
- mitigation documented for high-impact risks
- acceptance criteria explicit for residual risk
- risk ownership explicit

## Failure Mode Analysis

Before significant change:
- enumerate failure modes
- rank by likelihood and impact
- define detection methods
- define response playbook
- validate recovery path

No change ships without failure mode analysis when impact is high.

## Conflict Resolution

When priorities conflict:
1. consult higher priority first
2. consult relevant policy document
3. escalate to human decision-maker when clearance is unclear
4. record decision and reasoning
5. never assume future circumstances match past assumptions

## Operator Override

Operators may override SKYNET decisions when:
- they accept accountability
- the override is documented and attributed
- the impact is understood
- the override is within policy and law

Operator overrides become training data for future recommendations.
