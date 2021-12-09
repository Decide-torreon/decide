
export default class ChartService {

  constructor(repository) {
    this._repository = repository;
  }

  async countVotingsGroupedByState() {
    const votings = await this._repository.listVotings();
    
    const group = votings.reduce((group, voting) => {
      const { state } = voting;
      if (group[state.code] == null) {
        group[state.code] = 0;
      }
      group[state.code] ++;

      return group;
    }, {})

    return group;
  }

}