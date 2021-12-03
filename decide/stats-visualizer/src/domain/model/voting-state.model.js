
export default class VotingState {

  constructor({ code, name }) {
    this.__code = code;
    this.__name = name;
  }

  get code() {
    return this.__code;
  }

  get name() {
    return this.__name;
  }

}

const createVotingState = (code, name ) => new VotingState({ code, name });

const VOTING_STATES = {
  notStarted: createVotingState('NOT_STARTED', 'No empezada'),
  started: createVotingState('STARTED', 'Empezada'),
  finished: createVotingState('FINISHED', 'Terminada'),
};

export { VOTING_STATES };