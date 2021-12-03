
export default class VotingService {

  constructor(repository) {
    this._repository = repository;
  }

  findAll(page) {
    return this._repository.listVotings();
  }

  findById(id) {
    return this._repository.getVoting(id);
  }

}